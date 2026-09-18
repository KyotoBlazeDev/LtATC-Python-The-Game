import logging
from math import isfinite
from dataclasses import dataclass
from game.aircraft import Aircraft, AircraftState
from game.clearances import Clearance, ClearanceType
from game.constants import AIRCRAFT_LIMIT, GameMode
from game.runway import Runway
from game.safety import SafetySystem, ValidationResult
from game.collision import find_collision

@dataclass
class Metrics:
    clearances_attempted: int = 0
    clearances_transmitted: int = 0
    unsafe_clearances_prevented: int = 0
    self_corrections: int = 0
    instructor_interventions: int = 0

class Simulation:
    def __init__(self) -> None:
        self.aircraft: dict[str, Aircraft] = {}
        self.runway = Runway()
        self.safety = SafetySystem()
        self.mode = GameMode.MAIN_MENU
        self.speed = 1.0
        self.paused = False
        self.training_safety = True
        self.separation_warnings = True
        self.metrics = Metrics()
        self.selected_callsign: str | None = None
        self.collision = None

    @property
    def game_over(self):
        return self.collision is not None

    def reset(self, mode: GameMode) -> None:
        self.aircraft.clear()
        self.runway = Runway()
        self.mode = mode
        self.speed = 1.0
        self.paused = False
        self.training_safety = True
        self.separation_warnings = True
        self.safety.reset_thresholds()
        self.metrics = Metrics()
        self.selected_callsign = None
        self.collision = None

    def spawn_aircraft(self, aircraft: Aircraft) -> bool:
        if self.game_over or len(self.aircraft) >= AIRCRAFT_LIMIT or aircraft.callsign in self.aircraft:
            return False
        self.aircraft[aircraft.callsign] = aircraft
        return True

    def remove_aircraft(self, callsign: str) -> None:
        if self.game_over:
            return
        self.aircraft.pop(callsign, None)
        if self.selected_callsign == callsign:
            self.select(None)
        if self.runway.occupied_by == callsign:
            self.runway.occupied_by = None

    def get_aircraft(self, callsign: str | None) -> Aircraft | None:
        return self.aircraft.get(callsign) if callsign else None

    def select(self, callsign: str | None) -> None:
        self.selected_callsign = callsign if callsign in self.aircraft else None
        for plane in self.aircraft.values():
            plane.selected = plane.callsign == self.selected_callsign

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        if not self.game_over:
            self.paused = False

    def set_speed(self, multiplier: float) -> None:
        if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)) or not isfinite(multiplier):
            raise ValueError("Simulation speed must be a finite number.")
        if not 0.25 <= multiplier <= 4.0:
            raise ValueError("Simulation speed must be between 0.25x and 4.0x.")
        self.speed = float(multiplier)

    def update(self, dt: float) -> None:
        if self.paused or self.game_over:
            return
        if isinstance(dt, bool) or not isinstance(dt, (int, float)) or not isfinite(dt) or dt < 0:
            raise ValueError("Simulation time step must be a finite, nonnegative number.")
        interactive = self.mode in {GameMode.LESSON, GameMode.SANDBOX}
        if interactive and self.training_safety and any(
                c.critical for c in self.safety.conflicts(list(self.aircraft.values()), predict=False)):
            self.pause()
            return
        previous = {p.callsign: (p.x, p.y, p.altitude) for p in self.aircraft.values()}
        for plane in list(self.aircraft.values()):
            try:
                plane.update(min(dt * self.speed, .2))
            except (TypeError, ValueError, OverflowError):
                logging.exception("Could not update %s", plane.callsign)
        if interactive:
            impact = find_collision(self.aircraft.values(), previous)
            if impact and not self.training_safety:
                fraction, self.collision = impact
                for plane in self.aircraft.values():
                    x, y, altitude = previous[plane.callsign]
                    plane.x = x + (plane.x - x) * fraction
                    plane.y = y + (plane.y - y) * fraction
                    plane.altitude = round(altitude + (plane.altitude - altitude) * fraction)
                self.pause()
            elif self.training_safety and (impact or any(
                    c.critical for c in self.safety.conflicts(list(self.aircraft.values()), predict=False))):
                self.pause()
        if self.runway.occupied_by:
            occupant = self.get_aircraft(self.runway.occupied_by)
            if occupant is None or not occupant.on_runway:
                self.runway.occupied_by = None

    def transmit(self, callsign: str, clearance: Clearance) -> ValidationResult:
        if self.game_over:
            return ValidationResult(False, "WARNING", "Game over. Retry or return to the main menu.")
        plane = self.get_aircraft(callsign)
        self.metrics.clearances_attempted += 1
        if plane is None:
            return ValidationResult(False, "WARNING", "Select an aircraft first.")
        result = self.safety.validate(self, plane, clearance)
        if not result.safe:
            self.metrics.unsafe_clearances_prevented += 1
            logging.debug("Unsafe %s request blocked: %s", clearance.clearance_type.name, result.message)
            return result
        self.metrics.clearances_transmitted += 1
        kind, value = clearance.clearance_type, clearance.value
        if kind == ClearanceType.TAKEOFF:
            plane.state, plane.on_runway = AircraftState.TAKEOFF_ROLL, True
            self.runway.occupied_by = callsign
            plane.target_heading = self.runway.heading
        elif kind == ClearanceType.LINE_UP_AND_WAIT:
            plane.state, plane.on_runway = AircraftState.LINE_UP, True
            self.runway.occupied_by = callsign
        elif kind == ClearanceType.HEADING and value is not None:
            plane.target_heading = value % 360
        elif kind == ClearanceType.ALTITUDE and value is not None:
            plane.target_altitude = value
        elif kind == ClearanceType.SPEED and value is not None:
            plane.target_speed = value
        elif kind == ClearanceType.APPROACH:
            plane.state = AircraftState.APPROACH
            plane.target_heading = self.runway.heading
        elif kind == ClearanceType.LAND:
            plane.state, plane.on_runway = AircraftState.LANDING, True
            plane.target_altitude = 0
            plane.target_speed = 65
            self.runway.occupied_by = callsign
        elif kind == ClearanceType.GO_AROUND:
            plane.state, plane.on_runway = AircraftState.CLIMBING, False
            plane.target_altitude = max(2000, plane.altitude)
            plane.target_speed = 110
            if self.runway.occupied_by == callsign:
                self.runway.occupied_by = None
        elif kind == ClearanceType.HOLD:
            plane.state = AircraftState.HOLDING
            plane.target_speed = 70 if plane.altitude else 0
        return result
