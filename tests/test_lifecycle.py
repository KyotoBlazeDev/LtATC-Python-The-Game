"""Regression checks for scene and actor lifetime ownership."""
import unittest

from game.constants import GameMode
from game.game_state import GameState


class LifecycleTests(unittest.TestCase):
    def test_repeated_lesson_start_does_not_respawn_actors(self):
        game = GameState()
        self.assertTrue(game.start_lesson("03"))
        lesson = game.lessons.current
        aircraft = game.simulation.aircraft.copy()
        self.assertFalse(game.start_lesson("03"))
        self.assertIs(game.lessons.current, lesson)
        self.assertEqual(game.simulation.aircraft, aircraft)
        self.assertEqual(len(game.simulation.aircraft), 2)
        self.assertTrue(game.start_lesson("03", restart=True))
        self.assertIsNot(game.lessons.current, lesson)
        self.assertEqual(len(game.simulation.aircraft), 2)

    def test_repeated_story_start_and_menu_cleanup(self):
        game = GameState()
        self.assertTrue(game.start_chapter("01"))
        chapter = game.story_manager.current
        self.assertFalse(game.start_chapter("01"))
        self.assertIs(game.story_manager.current, chapter)
        self.assertEqual(set(game.simulation.aircraft), {"NWA299", "NWA1482"})
        game.enter_menu()
        self.assertEqual(game.simulation.mode, GameMode.MAIN_MENU)
        self.assertFalse(game.simulation.aircraft)
        self.assertIsNone(game.story_manager.current)
        self.assertTrue(game.start_chapter("01"))
        self.assertIsNot(game.story_manager.current, chapter)

    def test_modes_do_not_keep_each_others_actors(self):
        game = GameState()
        game.start_lesson("03")
        game.enter_menu()
        game.start_sandbox()
        self.assertEqual(set(game.simulation.aircraft), {"ACADEMY 02"})
        self.assertFalse(game.start_sandbox())
        self.assertEqual(set(game.simulation.aircraft), {"ACADEMY 02"})
        game.enter_menu()
        game.start_chapter("01")
        self.assertNotIn("ACADEMY 02", game.simulation.aircraft)

    def test_completion_recorded_only_once(self):
        game = GameState()
        game.start_lesson("01")
        self.assertTrue(game.complete_lesson("01"))
        self.assertFalse(game.complete_lesson("01"))
        self.assertEqual(game.story.student_competence, 1)
        game.enter_menu()
        game.start_chapter("01")
        self.assertTrue(game.complete_chapter("01"))
        self.assertFalse(game.complete_chapter("01"))
        self.assertEqual(game.story.student_competence, 2)

    def test_invalid_scene_cannot_reset_active_session(self):
        game = GameState()
        game.start_lesson("03")
        with self.assertRaises(ValueError):
            game.start_lesson("99")
        self.assertEqual(game.active_id, "03")
        self.assertEqual(len(game.simulation.aircraft), 2)
        with self.assertRaises(ValueError):
            game.start_chapter("02")
        self.assertEqual(game.simulation.mode, GameMode.LESSON)

    def test_managers_reject_overlapping_scene_starts(self):
        game = GameState()
        game.start_lesson("03")
        self.assertIs(game.lessons.start("03", game.simulation), game.lessons.current)
        with self.assertRaises(RuntimeError):
            game.lessons.start("02", game.simulation)
        game.enter_menu()
        game.story.chapters_completed.add("01")
        game.start_chapter("01")
        self.assertIs(game.story_manager.start("01", game.simulation), game.story_manager.current)
        with self.assertRaises(RuntimeError):
            game.story_manager.start("02", game.simulation)


if __name__ == "__main__":
    unittest.main()
