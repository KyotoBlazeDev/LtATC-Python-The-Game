"""Regression checks for validation, runway state, and persistent progress."""
from math import inf, nan
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from game.aircraft import Aircraft, AircraftState
from game.clearances import Clearance, ClearanceType as C
from game.constants import GameMode
from game.game_state import GameState
from game.runway import Runway
from game.simulation import Simulation
from story.persistence import load_progress, save_progress
from story.story_state import StoryState


class HardeningTests(unittest.TestCase):
    def airborne_simulation(self):
        simulation = Simulation()
        simulation.reset(GameMode.SANDBOX)
        simulation.spawn_aircraft(Aircraft(
            "TEST 01", 100, 100, altitude=3000, speed=90,
            target_altitude=3000, target_speed=90, state=AircraftState.AIRBORNE,
        ))
        return simulation

    def test_vector_clearances_require_finite_values_in_training_ranges(self):
        simulation = self.airborne_simulation()
        invalid = (
            Clearance(C.HEADING), Clearance(C.HEADING, nan), Clearance(C.HEADING, 361),
            Clearance(C.ALTITUDE, -1), Clearance(C.ALTITUDE, inf),
            Clearance(C.SPEED, 29), Clearance(C.SPEED, 251), Clearance(C.SPEED, True),
        )
        for clearance in invalid:
            with self.subTest(clearance=clearance):
                self.assertFalse(simulation.transmit("TEST 01", clearance).safe)
        self.assertTrue(simulation.transmit("TEST 01", Clearance(C.HEADING, 360)).safe)
        self.assertTrue(simulation.transmit("TEST 01", Clearance(C.SPEED, 130)).safe)

    def test_speed_and_time_step_validation(self):
        simulation = self.airborne_simulation()
        for value in (-1, 0, 4.1, inf, nan, True):
            with self.subTest(speed=value), self.assertRaises(ValueError):
                simulation.set_speed(value)
        simulation.set_speed(4)
        self.assertEqual(simulation.speed, 4.0)
        for value in (-0.1, inf, nan, True):
            with self.subTest(dt=value), self.assertRaises(ValueError):
                simulation.update(value)

    def test_go_around_preserves_another_aircrafts_runway_occupancy(self):
        simulation = self.airborne_simulation()
        simulation.get_aircraft("TEST 01").state = AircraftState.APPROACH
        simulation.spawn_aircraft(Aircraft("ON RUNWAY", 200, 200, state=AircraftState.LINE_UP, on_runway=True))
        simulation.runway.occupied_by = "ON RUNWAY"
        self.assertTrue(simulation.transmit("TEST 01", Clearance(C.GO_AROUND)).safe)
        self.assertEqual(simulation.runway.occupied_by, "ON RUNWAY")

    def test_clearances_follow_runway_designator(self):
        simulation = self.airborne_simulation()
        simulation.runway.name = "04L"
        self.assertEqual(simulation.runway.heading, 40)
        self.assertTrue(simulation.transmit("TEST 01", Clearance(C.APPROACH)).safe)
        self.assertEqual(simulation.get_aircraft("TEST 01").target_heading, 40)
        with self.assertRaises(ValueError):
            Runway(name="40X").heading

    def test_progress_round_trip_and_corrupt_file_fallback(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            state = StoryState(student_competence=3, lessons_completed={"01"}, chapters_completed={"01", "02"})
            save_progress(path, state)
            restored = load_progress(path)
            self.assertEqual(restored.student_competence, 3)
            self.assertEqual(restored.lessons_completed, {"01"})
            self.assertEqual(restored.chapters_completed, {"01", "02"})
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(load_progress(path), StoryState())

    def test_game_completion_is_saved_and_resettable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            game = GameState(path)
            game.start_lesson("01")
            self.assertTrue(game.complete_lesson("01"))
            self.assertIn("01", GameState(path).story.lessons_completed)
            game.reset_progress()
            self.assertEqual(GameState(path).story, StoryState())

    def test_failed_save_does_not_claim_or_keep_completion(self):
        game = GameState(Path("unwritten-progress.json"))
        game.start_lesson("01")
        with patch("game.game_state.save_progress", side_effect=OSError("disk full")):
            self.assertFalse(game.complete_lesson("01"))
        self.assertNotIn("01", game.story.lessons_completed)
        self.assertEqual(game.story.student_competence, 0)
        self.assertFalse(game.completion_recorded)

    def test_replaying_content_does_not_repeat_rewards(self):
        game = GameState()
        game.start_lesson("01")
        self.assertTrue(game.complete_lesson("01"))
        game.start_lesson("01", restart=True)
        self.assertTrue(game.complete_lesson("01"))
        self.assertEqual(game.story.student_competence, 1)

    def test_failed_reset_keeps_current_progress(self):
        game = GameState(Path("unwritten-progress.json"))
        game.story.lessons_completed.add("01")
        with patch("game.game_state.save_progress", side_effect=OSError("disk full")):
            self.assertFalse(game.reset_progress())
        self.assertIn("01", game.story.lessons_completed)


if __name__ == "__main__":
    unittest.main()
