import random
from math import isfinite
from game.aircraft import Aircraft, AircraftState
from game.constants import AIRCRAFT_LIMIT, GameMode

class SandboxManager:
    def __init__(self, simulation) -> None:
        self.simulation = simulation
        self.next_number = 2
        self.traffic_rate = "Manual"
        self.weather = "Clear"
        self.time_of_day = "Day"
        self.emergencies = False
        self._traffic_elapsed = 0.0
        self._previous_rate = "Manual"
        self.challenge_active = False
        self.challenge_finished = False
        self.challenge_elapsed = 0.0
        self.challenge_handled = 0
        self.challenge_missed = 0
        self.challenge_safe_seconds = 0.0
        self.challenge_report = ""
        self._emergency_elapsed = 0.0
        self._closure_remaining = 0.0
        self._next_emergency = "priority"
        self.messages = []

    def assign_destination(self, plane):
        if not plane.destination:
            plane.destination = random.choice(("LAND", "NORTH", "EAST", "SOUTH", "WEST"))

    @staticmethod
    def reached_destination(plane):
        if plane.destination == "LAND":
            return plane.state == AircraftState.PARKED and plane.altitude == 0
        if plane.altitude <= 0:
            return False
        return {
            "NORTH": plane.y < -30 and abs(plane.x - 350) <= 80,
            "SOUTH": plane.y > 620 and abs(plane.x - 350) <= 80,
            "WEST": plane.x < -30 and abs(plane.y - 295) <= 80,
            "EAST": plane.x > 730 and abs(plane.y - 295) <= 80,
        }.get(plane.destination, False)

    def start_challenge(self):
        self.simulation.session_finished = False
        self.challenge_active = True
        self.challenge_finished = False
        self.challenge_elapsed = self.challenge_safe_seconds = 0.0
        self.challenge_handled = 0
        self.challenge_missed = 0
        self.traffic_rate = "Low"
        self.messages.append("Three-minute shift started. Guide traffic out of the sector or land it; keep separation. Traffic increases each minute.")

    def trigger_emergency(self):
        sim = self.simulation
        if sim.mode != GameMode.SANDBOX or sim.game_over or self.challenge_finished:
            return False
        if self._next_emergency == "closure":
            if sim.runway.closed or sim.runway.occupied_by:
                return False
            sim.runway.closed = True
            self._closure_remaining = 15.0
            self._next_emergency = "priority"
            self.messages.append("Runway inspection: runway closed for 15 simulation seconds. Go around any approaching traffic; landing clearances are blocked.")
            return True
        plane = next((p for p in sim.aircraft.values() if p.altitude > 0 and not p.emergency), None)
        if plane is None or any(p.emergency for p in sim.aircraft.values()):
            return False
        plane.emergency = True
        plane.destination = "LAND"
        self._next_emergency = "closure"
        self.messages.append(f"{plane.callsign}: priority landing requested. Select this aircraft, arrange an approach, check runway availability, and land.")
        return True

    def _advance_session(self, seconds):
        sim = self.simulation
        if self._closure_remaining:
            self._closure_remaining = max(0.0, self._closure_remaining - seconds)
            if self._closure_remaining < 1e-9:
                self._closure_remaining = 0.0
                sim.runway.closed = False
                self.messages.append("Runway inspection complete: runway reopened.")
        for plane in list(sim.aircraft.values()):
            self.assign_destination(plane)
            landed = plane.state == AircraftState.PARKED and plane.altitude == 0
            exited = plane.x < -30 or plane.x > 730 or plane.y < -30 or plane.y > 620
            if plane.emergency and landed:
                plane.emergency = False
                self.messages.append(f"{plane.callsign}: priority landing complete.")
            if exited or (landed and self.challenge_active):
                if self.challenge_active:
                    if self.reached_destination(plane):
                        self.challenge_handled += 1
                    else:
                        self.challenge_missed += 1
                outcome = "Assignment complete" if self.reached_destination(plane) else "Destination missed"
                self.messages.append(f"{plane.callsign}: {outcome} ({plane.destination}).")
                sim.remove_aircraft(plane.callsign)
        if self.emergencies:
            self._emergency_elapsed += seconds
            if self._emergency_elapsed >= 30:
                self._emergency_elapsed = 0.0
                self.trigger_emergency()
        else:
            self._emergency_elapsed = 0.0
        if self.challenge_active:
            self.challenge_elapsed = min(180.0, self.challenge_elapsed + seconds)
            if not sim.safety.conflicts(list(sim.aircraft.values()), predict=False):
                self.challenge_safe_seconds += seconds
            self.traffic_rate = "Low" if self.challenge_elapsed < 60 else "Medium" if self.challenge_elapsed < 120 else "High"
            if self.challenge_elapsed >= 180 - 1e-9:
                self.finish_challenge()

    def finish_challenge(self, failed=False):
        self.challenge_active = False
        self.challenge_finished = True
        score = self.challenge_handled * 100 + round(self.challenge_safe_seconds)
        self.challenge_report = (f"{'Shift ended by collision' if failed else 'Shift complete'}\n"
            f"Assignments completed: {self.challenge_handled}\n"
            f"Destinations missed: {self.challenge_missed}\n"
            f"Seconds with separation: {round(self.challenge_safe_seconds)}\n"
            f"Unsafe commands prevented: {self.simulation.metrics.unsafe_clearances_prevented}\n"
            f"Score: {score}\nRetry starts a fresh Sandbox; Start shift starts a new challenge.")
        self.simulation.pause()
        self.simulation.session_finished = True

    def update(self, dt: float) -> Aircraft | None:
        """Generate at most one arrival per tick, measured in simulation seconds."""
        if isinstance(dt, bool) or not isinstance(dt, (int, float)) or not isfinite(dt) or dt < 0:
            raise ValueError("Traffic time step must be finite and nonnegative.")
        if self.traffic_rate != self._previous_rate:
            self._traffic_elapsed = 0.0
            self._previous_rate = self.traffic_rate
        interval = {"Low": 20.0, "Medium": 10.0, "High": 5.0}.get(self.traffic_rate)
        sim = self.simulation
        if sim.mode != GameMode.SANDBOX or self.challenge_finished:
            return None
        if sim.game_over:
            if self.challenge_active:
                self.finish_challenge(failed=True)
            return None
        if sim.paused:
            return None
        seconds = min(dt * sim.speed, .2)
        self._advance_session(seconds)
        if self.challenge_finished:
            return None
        interval = {"Low": 20.0, "Medium": 10.0, "High": 5.0}.get(self.traffic_rate)
        if interval is None:
            return None
        self._traffic_elapsed += seconds
        if self._traffic_elapsed + 1e-9 < interval:
            return None
        self._traffic_elapsed = 0.0
        if len(sim.aircraft) >= AIRCRAFT_LIMIT:
            return None
        # Enter from the radar edge; avoid creating an immediate predicted conflict.
        for _ in range(20):
            x, y, heading = random.choice(((80, 250, 90), (620, 250, 270),
                                           (350, 80, 180), (350, 550, 0)))
            altitude = random.choice((2000, 3000, 4000, 5000))
            while f"ACADEMY {self.next_number:02d}" in sim.aircraft:
                self.next_number += 1
            plane = Aircraft(f"ACADEMY {self.next_number:02d}", x, y, heading,
                             altitude, 90, heading, altitude, 90, AircraftState.AIRBORNE)
            conflicts = sim.safety.conflicts([*sim.aircraft.values(), plane])
            if any(plane.callsign in (c.first, c.second) for c in conflicts):
                continue
            self.assign_destination(plane)
            if sim.spawn_aircraft(plane):
                self.next_number += 1
                return plane
        return None

    def spawn(self) -> Aircraft | None:
        if self.simulation.game_over or self.simulation.session_finished or len(self.simulation.aircraft) >= AIRCRAFT_LIMIT:
            return None
        while f"ACADEMY {self.next_number:02d}" in self.simulation.aircraft:
            self.next_number += 1
        callsign = f"ACADEMY {self.next_number:02d}"
        self.next_number += 1
        heading = random.choice((45, 90, 135, 180, 225, 270, 315))
        altitude = random.choice((2000, 3000, 4000, 5000))
        speed = random.randrange(70, 121)
        plane = Aircraft(callsign, random.randrange(90, 610), random.randrange(85, 560), heading,
                         altitude, speed, heading, altitude, speed, AircraftState.AIRBORNE)
        self.assign_destination(plane)
        return plane if self.simulation.spawn_aircraft(plane) else None
