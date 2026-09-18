"""Small event vocabulary shared by story and presentation code."""
from dataclasses import dataclass
from enum import Enum, auto

class EventType(Enum):
    AIRCRAFT_SPAWNED = auto()
    AIRCRAFT_SELECTED = auto()
    CLEARANCE_ATTEMPTED = auto()
    CLEARANCE_TRANSMITTED = auto()
    SEPARATION_WARNING = auto()
    SAFETY_BOUNDARY_TRIGGERED = auto()
    OBJECTIVE_COMPLETED = auto()
    DIALOGUE_FINISHED = auto()
    CHAPTER_COMPLETED = auto()

@dataclass(frozen=True)
class GameEvent:
    kind: EventType
    callsign: str | None = None
    detail: str = ""
