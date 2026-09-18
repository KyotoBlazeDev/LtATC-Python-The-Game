from enum import Enum, auto

class GameMode(Enum):
    MAIN_MENU = auto()
    STORY = auto()
    LESSON = auto()
    SANDBOX = auto()

AIRCRAFT_LIMIT = 30
HORIZONTAL_WARNING = 80.0
HORIZONTAL_CRITICAL = 40.0
VERTICAL_WARNING = 1000
