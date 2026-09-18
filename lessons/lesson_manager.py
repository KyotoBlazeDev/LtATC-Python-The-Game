from lessons.lesson_01_departure import DepartureLesson
from lessons.lesson_02_heading import HeadingLesson
from lessons.lesson_03_separation import SeparationLesson
from game.constants import GameMode

LESSONS = (DepartureLesson, HeadingLesson, SeparationLesson)

class LessonManager:
    def __init__(self) -> None:
        self.current = None

    def start(self, lesson_id: str, simulation):
        lesson_class = next((item for item in LESSONS if item.lesson_id == lesson_id), None)
        if lesson_class is None:
            raise ValueError(f"Unknown lesson {lesson_id}")
        if self.current is not None and simulation.mode == GameMode.LESSON:
            if self.current.lesson_id == lesson_id:
                return self.current
            raise RuntimeError("Exit the active lesson before starting another")
        self.current = lesson_class()
        self.current.start(simulation)
        return self.current
