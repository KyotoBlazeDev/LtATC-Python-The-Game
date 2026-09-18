from dataclasses import dataclass
from enum import Enum, auto

class ClearanceType(Enum):
    TAKEOFF = auto()
    LAND = auto()
    GO_AROUND = auto()
    HOLD = auto()
    HEADING = auto()
    ALTITUDE = auto()
    SPEED = auto()
    LINE_UP_AND_WAIT = auto()
    APPROACH = auto()

@dataclass(frozen=True)
class Clearance:
    clearance_type: ClearanceType
    value: int | None = None
