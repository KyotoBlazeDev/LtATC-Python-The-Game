from dataclasses import dataclass
from enum import Enum, auto
from math import atan2, cos, degrees, hypot, radians, sin

class AircraftState(Enum):
    PARKED = auto()
    TAXI = auto()
    HOLDING_SHORT = auto()
    LINE_UP = auto()
    TAKEOFF_ROLL = auto()
    CLIMBING = auto()
    AIRBORNE = auto()
    APPROACH = auto()
    LANDING = auto()
    LANDED = auto()
    HOLDING = auto()

@dataclass
class Aircraft:
    callsign: str
    x: float
    y: float
    heading: float = 270
    altitude: int = 0
    speed: float = 0
    target_heading: float = 270
    target_altitude: int = 0
    target_speed: float = 0
    state: AircraftState = AircraftState.PARKED
    selected: bool = False
    emergency: bool = False
    on_runway: bool = False

    def update(self, dt: float) -> None:
        if self.state == AircraftState.TAKEOFF_ROLL:
            self.target_speed = 110
            self.target_altitude = 3000
            if self.speed >= 75:
                self.state = AircraftState.CLIMBING
                self.on_runway = False
        if self.state == AircraftState.LANDING and self.altitude <= 0:
            self.state = AircraftState.LANDED
            self.target_speed = 0
        turn = (self.target_heading - self.heading + 180) % 360 - 180
        self.heading = (self.heading + max(-35 * dt, min(35 * dt, turn))) % 360
        self.speed += max(-35 * dt, min(35 * dt, self.target_speed - self.speed))
        climb = max(-500 * dt, min(500 * dt, self.target_altitude - self.altitude))
        self.altitude = max(0, round(self.altitude + climb))
        if self.state == AircraftState.CLIMBING and self.altitude >= 500:
            self.state = AircraftState.AIRBORNE
        if self.state == AircraftState.LANDED and self.speed < 1:
            self.state = AircraftState.PARKED
            self.on_runway = False
        if self.state not in {AircraftState.PARKED, AircraftState.HOLDING_SHORT, AircraftState.LINE_UP, AircraftState.LANDED} and (self.altitude > 0 or self.state in {AircraftState.TAKEOFF_ROLL, AircraftState.LANDING}):
            self.x += self.speed * sin(radians(self.heading)) * dt * .3
            self.y -= self.speed * cos(radians(self.heading)) * dt * .3

    def predicted_position(self, seconds: float) -> tuple[float, float]:
        h = radians(self.target_heading)
        return self.x + self.target_speed * sin(h) * seconds * .3, self.y - self.target_speed * cos(h) * seconds * .3
