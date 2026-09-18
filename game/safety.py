from dataclasses import dataclass
from copy import copy
from math import cos, hypot, radians, sin
from math import isfinite
from game.aircraft import Aircraft, AircraftState
from game.clearances import Clearance, ClearanceType
from game.constants import HORIZONTAL_WARNING, HORIZONTAL_CRITICAL, VERTICAL_WARNING

@dataclass(frozen=True)
class ValidationResult:
    safe: bool
    severity: str = "INFO"
    message: str = "Clearance verified."

@dataclass(frozen=True)
class Conflict:
    first: str
    second: str
    distance: float
    critical: bool

class SafetySystem:
    def __init__(self, horizontal_warning=HORIZONTAL_WARNING,
                 horizontal_critical=HORIZONTAL_CRITICAL,
                 vertical_warning=VERTICAL_WARNING):
        self.set_thresholds(horizontal_warning, horizontal_critical, vertical_warning)

    def set_thresholds(self, horizontal_warning, horizontal_critical, vertical_warning):
        horizontal_warning = float(horizontal_warning)
        horizontal_critical = float(horizontal_critical)
        vertical_warning = int(vertical_warning)
        if not isfinite(horizontal_warning) or not isfinite(horizontal_critical):
            raise ValueError("Safety thresholds must be finite.")
        if horizontal_warning <= 0 or horizontal_critical <= 0 or vertical_warning <= 0:
            raise ValueError("Safety thresholds must be positive.")
        if horizontal_critical > horizontal_warning:
            raise ValueError("Critical horizontal distance cannot exceed warning distance.")
        self.horizontal_warning = horizontal_warning
        self.horizontal_critical = horizontal_critical
        self.vertical_warning = vertical_warning

    def reset_thresholds(self):
        self.set_thresholds(HORIZONTAL_WARNING, HORIZONTAL_CRITICAL, VERTICAL_WARNING)

    def validate(self, simulation, aircraft: Aircraft, clearance: Clearance) -> ValidationResult:
        kind = clearance.clearance_type
        ground = {AircraftState.PARKED, AircraftState.HOLDING_SHORT, AircraftState.LINE_UP, AircraftState.LANDED}
        if kind in {ClearanceType.TAKEOFF, ClearanceType.LINE_UP_AND_WAIT}:
            if aircraft.state not in ground:
                return ValidationResult(False, "WARNING", "Aircraft is not ready on the ground.")
            if simulation.runway.closed or not simulation.runway.departure_enabled:
                return ValidationResult(False, "WARNING", f"Runway {simulation.runway.name} is unavailable for departure.")
            if simulation.runway.occupied_by not in {None, aircraft.callsign}:
                return ValidationResult(False, "WARNING", f"Runway {simulation.runway.name} is occupied by {simulation.runway.occupied_by}.")
        if kind in {ClearanceType.LAND, ClearanceType.APPROACH}:
            if aircraft.state in ground:
                return ValidationResult(False, "WARNING", "An aircraft on the ground cannot land.")
            if simulation.runway.closed or not simulation.runway.arrival_enabled or simulation.runway.occupied_by not in {None, aircraft.callsign}:
                return ValidationResult(False, "WARNING", f"Runway {simulation.runway.name} is unavailable for arrival.")
        if kind == ClearanceType.GO_AROUND and aircraft.state not in {AircraftState.APPROACH, AircraftState.LANDING}:
            return ValidationResult(False, "WARNING", "Go-around requires an approach or landing aircraft.")
        if kind in {ClearanceType.HEADING, ClearanceType.ALTITUDE, ClearanceType.SPEED} and aircraft.state in ground:
            return ValidationResult(False, "WARNING", "Select an airborne aircraft for this clearance.")
        if kind in {ClearanceType.HEADING, ClearanceType.ALTITUDE, ClearanceType.SPEED}:
            value = clearance.value
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                return ValidationResult(False, "WARNING", f"{kind.name.title()} requires a finite numeric value.")
            limits = {
                ClearanceType.HEADING: (0, 360),
                ClearanceType.ALTITUDE: (0, 10000),
                ClearanceType.SPEED: (30, 250),
            }
            lower, upper = limits[kind]
            if not lower <= value <= upper:
                return ValidationResult(False, "WARNING", f"{kind.name.title()} is outside the training range ({lower}–{upper}).")
        if simulation.training_safety and kind in {
                ClearanceType.HEADING, ClearanceType.ALTITUDE, ClearanceType.SPEED
        } and clearance.value is not None:
            proposed = copy(aircraft)
            if kind == ClearanceType.HEADING:
                proposed.target_heading = clearance.value % 360
            elif kind == ClearanceType.ALTITUDE:
                proposed.target_altitude = clearance.value
            else:
                proposed.target_speed = clearance.value
            traffic = [proposed if item is aircraft else item for item in simulation.aircraft.values()]
            original_pairs = {
                frozenset((c.first, c.second)): c
                for c in self.conflicts(list(simulation.aircraft.values()))
            }
            for conflict in self.conflicts(traffic):
                original = original_pairs.get(frozenset((conflict.first, conflict.second)))
                if original is None or conflict.distance < original.distance - 1e-9:
                    return ValidationResult(False, "WARNING", f"Proposed clearance creates a predicted conflict with {conflict.second if conflict.first == aircraft.callsign else conflict.first}.")
        return ValidationResult(True)

    def _predicted_minimum(self, first: Aircraft, second: Aircraft, horizon: float = 8.0) -> float | None:
        """Return continuous closest horizontal distance while vertically unsafe.

        Horizontal prediction follows the existing target-vector model.  Vertical
        motion is piecewise linear because each aircraft stops climbing or
        descending when it reaches its target altitude.
        """
        first_heading = radians(first.target_heading)
        second_heading = radians(second.target_heading)
        relative_x = first.x - second.x
        relative_y = first.y - second.y
        velocity_x = .3 * (first.target_speed * sin(first_heading)
                           - second.target_speed * sin(second_heading))
        velocity_y = -.3 * (first.target_speed * cos(first_heading)
                            - second.target_speed * cos(second_heading))

        def climb_rate(plane):
            difference = plane.target_altitude - plane.altitude
            return 500.0 if difference > 0 else -500.0 if difference < 0 else 0.0

        first_rate, second_rate = climb_rate(first), climb_rate(second)
        breakpoints = {0.0, horizon}
        for plane, rate in ((first, first_rate), (second, second_rate)):
            if rate:
                breakpoints.add(min(horizon, abs(plane.target_altitude - plane.altitude) / 500.0))
        times = sorted(breakpoints)
        minimum = None
        velocity_squared = velocity_x * velocity_x + velocity_y * velocity_y

        for start, end in zip(times, times[1:]):
            midpoint = (start + end) / 2
            first_vertical_rate = first_rate if midpoint < abs(first.target_altitude - first.altitude) / 500.0 else 0.0
            second_vertical_rate = second_rate if midpoint < abs(second.target_altitude - second.altitude) / 500.0 else 0.0
            first_start_alt = first.altitude + first_rate * min(start, abs(first.target_altitude - first.altitude) / 500.0 if first_rate else 0)
            second_start_alt = second.altitude + second_rate * min(start, abs(second.target_altitude - second.altitude) / 500.0 if second_rate else 0)
            vertical_difference = first_start_alt - second_start_alt
            vertical_rate = first_vertical_rate - second_vertical_rate
            unsafe_start, unsafe_end = start, end
            if vertical_rate:
                crossings = sorted((start + (-self.vertical_warning - vertical_difference) / vertical_rate,
                                    start + (self.vertical_warning - vertical_difference) / vertical_rate))
                unsafe_start, unsafe_end = max(start, crossings[0]), min(end, crossings[1])
            elif abs(vertical_difference) >= self.vertical_warning:
                continue
            if unsafe_start >= unsafe_end:
                continue
            candidates = [unsafe_start, unsafe_end]
            if velocity_squared:
                closest = -(relative_x * velocity_x + relative_y * velocity_y) / velocity_squared
                candidates.append(max(unsafe_start, min(unsafe_end, closest)))
            distance = min(hypot(relative_x + velocity_x * time,
                                 relative_y + velocity_y * time) for time in candidates)
            minimum = distance if minimum is None else min(minimum, distance)
        return minimum

    def conflicts(self, aircraft: list[Aircraft], predict: bool = True) -> list[Conflict]:
        active = [a for a in aircraft if a.altitude > 0 or a.state in {AircraftState.AIRBORNE, AircraftState.CLIMBING, AircraftState.APPROACH}]
        found = []
        for index, first in enumerate(active):
            for second in active[index + 1:]:
                actual_distance = hypot(first.x - second.x, first.y - second.y)
                if predict:
                    minimum_distance = self._predicted_minimum(first, second)
                else:
                    minimum_distance = (actual_distance if
                                        abs(first.altitude - second.altitude) < self.vertical_warning else None)
                if minimum_distance is not None and minimum_distance < self.horizontal_warning:
                    actual_vertical = abs(first.altitude - second.altitude)
                    found.append(Conflict(first.callsign, second.callsign, minimum_distance,
                                          actual_distance < self.horizontal_critical and actual_vertical < self.vertical_warning))
        return found
