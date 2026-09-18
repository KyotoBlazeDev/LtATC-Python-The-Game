"""Own the lifetime of the active menu, lesson, story chapter, or sandbox."""
import logging
from copy import deepcopy
from pathlib import Path
from game.aircraft import Aircraft, AircraftState
from game.constants import GameMode
from game.simulation import Simulation
from lessons.lesson_manager import LESSONS, LessonManager
from sandbox.sandbox_manager import SandboxManager
from story.story_manager import StoryManager
from story.story_state import StoryState
from story.persistence import load_progress, save_progress


class GameState:
    """The only place that resets a session and starts its actors.

    Repeated requests for the active scene are no-ops. An explicit restart
    replaces the simulation and scene together, so actors cannot accumulate.
    """

    def __init__(self, save_path: Path | None = None) -> None:
        self.simulation = Simulation()
        self.save_path = save_path
        self.story = load_progress(save_path) if save_path is not None else StoryState()
        self.lessons = LessonManager()
        self.story_manager = StoryManager(self.story)
        self.sandbox = SandboxManager(self.simulation)
        self.active_id: str | None = None
        self.completion_recorded = False

    def enter_menu(self) -> None:
        self.simulation.reset(GameMode.MAIN_MENU)
        self.active_id = None
        self.completion_recorded = False
        self.lessons.current = None
        self.story_manager.current = None

    def start_lesson(self, lesson_id: str, *, restart: bool = False) -> bool:
        if not any(lesson.lesson_id == lesson_id for lesson in LESSONS):
            raise ValueError(f"Unknown lesson {lesson_id}")
        if self.simulation.mode == GameMode.LESSON and self.active_id == lesson_id and not restart:
            return False
        self.simulation.reset(GameMode.LESSON)
        self.active_id = lesson_id
        self.completion_recorded = False
        self.story_manager.current = None
        self.lessons.current = None
        self.lessons.start(lesson_id, self.simulation)
        return True

    def start_chapter(self, chapter_id: str, *, restart: bool = False) -> bool:
        if self.simulation.mode == GameMode.STORY and self.active_id == chapter_id and not restart:
            return False
        if not self.story_manager.unlocked(chapter_id):
            raise ValueError("Chapter is locked")
        self.simulation.reset(GameMode.STORY)
        self.active_id = chapter_id
        self.completion_recorded = False
        self.lessons.current = None
        self.story_manager.current = None
        self.story_manager.start(chapter_id, self.simulation)
        return True

    def start_sandbox(self, *, restart: bool = False, collision_demo: bool = False) -> bool:
        if self.simulation.mode == GameMode.SANDBOX and not restart and not collision_demo:
            return False
        self.simulation.reset(GameMode.SANDBOX)
        self.active_id = None
        self.completion_recorded = False
        self.lessons.current = None
        self.story_manager.current = None
        self.sandbox = SandboxManager(self.simulation)
        if collision_demo:
            self.simulation.training_safety = False
            self.simulation.pause()
            for callsign, x, heading in (("ACADEMY 02", 230, 90), ("ACADEMY 03", 470, 270)):
                self.simulation.spawn_aircraft(Aircraft(
                    callsign, x, 250, heading=heading, altitude=3000, speed=100,
                    target_heading=heading, target_altitude=3000, target_speed=100,
                    state=AircraftState.AIRBORNE))
            return True
        self.simulation.spawn_aircraft(Aircraft("ACADEMY 02", 390, 280, heading=270, altitude=3000,
                                                speed=90, target_heading=270, target_altitude=3000,
                                                target_speed=90, state=AircraftState.AIRBORNE))
        return True

    def complete_lesson(self, lesson_id: str) -> bool:
        if self.simulation.game_over or self.simulation.mode != GameMode.LESSON or self.active_id != lesson_id or self.completion_recorded:
            return False
        previous = deepcopy(self.story.__dict__)
        first_completion = lesson_id not in self.story.lessons_completed
        self.story.lessons_completed.add(lesson_id)
        if first_completion:
            self.story.student_competence += 1
        if not self._save_progress():
            self.story.__dict__.clear()
            self.story.__dict__.update(previous)
            return False
        self.completion_recorded = True
        self.simulation.pause()
        return True

    def complete_chapter(self, chapter_id: str) -> bool:
        if self.simulation.mode != GameMode.STORY or self.active_id != chapter_id or self.completion_recorded:
            return False
        previous = deepcopy(self.story.__dict__)
        first_completion = chapter_id not in self.story.chapters_completed
        self.story.chapters_completed.add(chapter_id)
        if first_completion:
            self.story.student_competence += 1
            self.story.blaze_trust += 1
        if not self._save_progress():
            self.story.__dict__.clear()
            self.story.__dict__.update(previous)
            return False
        self.completion_recorded = True
        self.simulation.pause()
        return True

    def _save_progress(self) -> bool:
        if self.save_path is None:
            return True
        try:
            save_progress(self.save_path, self.story)
            return True
        except OSError:
            logging.exception("Progress could not be saved")
            return False

    def reset_progress(self) -> bool:
        """Clear all persisted learning progress while preserving the save location."""
        previous = self.story
        self.story = StoryState()
        self.story_manager = StoryManager(self.story)
        if self._save_progress():
            return True
        self.story = previous
        self.story_manager = StoryManager(self.story)
        return False
