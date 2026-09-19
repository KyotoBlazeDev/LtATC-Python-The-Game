"""Behavioral checks for the incident case studies and simulation."""
import unittest

from game.aircraft import Aircraft, AircraftState
from game.clearances import Clearance, ClearanceType as C
from game.constants import AIRCRAFT_LIMIT, GameMode
from game.simulation import Simulation
from lessons.lesson_manager import LessonManager
from sandbox.sandbox_manager import SandboxManager
from story.story_manager import StoryManager
from story.story_state import StoryState
from ui.radar_canvas import RadarCanvas
from ui.main_window import INCIDENT_CONTENT_WARNING


class GameplayTests(unittest.TestCase):
    def setUp(self):
        self.sim = Simulation()
        self.state = StoryState()
        self.manager = StoryManager(self.state)

    def start(self, chapter_id):
        self.sim.reset(GameMode.STORY)
        self.manager.current = None
        return self.manager.start(chapter_id, self.sim)

    def test_incident_menu_warns_about_real_fatalities_and_educational_context(self):
        warning = INCIDENT_CONTENT_WARNING.lower()
        self.assertIn("real aviation accidents and fatalities", warning)
        self.assertIn("safety education", warning)
        self.assertIn("not entertainment", warning)

    def test_documented_cases_have_sources_and_complete(self):
        from story.story_manager import CHAPTERS
        for case in CHAPTERS:
            year = int(case.date_location.split()[2])
            self.assertGreaterEqual(year, 1990)
            self.assertLessEqual(year, 1999)
            self.assertNotIn("2023", case.title)
            self.assertNotIn("2024", case.title)
            chapter = self.start(case.chapter_id)
            self.assertTrue(chapter.source_url.startswith("https://"))
            self.assertIn("NTSB", chapter.event_indicator)
            chapter.choose("review", self.sim, self.state)
            wrong = next(action for _, action in chapter.choices if action != chapter.correct_action)
            chapter.choose(wrong, self.sim, self.state)
            self.assertEqual(chapter.stage, "decision")
            chapter.choose(chapter.correct_action, self.sim, self.state)
            self.assertEqual(chapter.stage, "debrief")
            chapter.choose("outcome", self.sim, self.state)
            self.assertTrue(chapter.completed)
            self.state.chapters_completed.add(case.chapter_id)
        self.assertTrue(self.state.training_complete)

    def test_case_study_blocks_simulated_clearances(self):
        chapter = self.start("01")
        plane = self.sim.get_aircraft("NWA299")
        self.assertIsNotNone(plane)
        self.assertIsNotNone(chapter.validate_clearance(plane, Clearance(C.TAKEOFF), self.sim))

    def test_checkpoint_restores_case_decision(self):
        chapter = self.start("01")
        chapter.choose("review", self.sim, self.state)
        chapter.choose(chapter.correct_action, self.sim, self.state)
        chapter.retry_checkpoint(self.sim, self.state)
        self.assertEqual(chapter.stage, "debrief")
        chapter.choose("outcome", self.sim, self.state)
        self.assertTrue(chapter.completed)

    def test_story_aircraft_fit_narrow_radar(self):
        # The 900px minimum window leaves roughly 540px for the radar.
        for x in (610, 620):
            screen_x, _ = RadarCanvas.screen_position(x, 270, 540, 500)
            self.assertLess(screen_x + 24, 540)

    def test_lessons_and_sandbox_still_work(self):
        self.sim.reset(GameMode.LESSON)
        LessonManager().start("01", self.sim)
        self.assertFalse(self.sim.transmit("CARGO 90", Clearance(C.LAND)).safe)
        self.sim.reset(GameMode.SANDBOX)
        sandbox = SandboxManager(self.sim)
        for _ in range(AIRCRAFT_LIMIT):
            plane = sandbox.spawn()
            self.assertIsNotNone(plane)
            self.assertTrue(plane.callsign.startswith("ACADEMY "))
        self.assertIsNone(sandbox.spawn())

    def test_lessons_use_story_document_aircraft_names(self):
        expected = {"01": {"CARGO 90"}, "02": {"ACADEMY 01"},
                    "03": {"EAGLE 21", "JET 404"}}
        for lesson_id, callsigns in expected.items():
            self.sim.reset(GameMode.LESSON)
            manager = LessonManager()
            manager.start(lesson_id, self.sim)
            self.assertEqual(set(self.sim.aircraft), callsigns)
            self.assertFalse(any(name.startswith("TRAINER") for name in self.sim.aircraft))

    def test_new_predicted_conflict_is_blocked(self):
        self.sim.reset(GameMode.SANDBOX)
        self.sim.spawn_aircraft(Aircraft("A", 100, 200, 0, 3000, 100, 0, 3000, 100, AircraftState.AIRBORNE))
        self.sim.spawn_aircraft(Aircraft("B", 300, 200, 0, 3000, 0, 0, 3000, 0, AircraftState.AIRBORNE))
        self.assertFalse(self.sim.transmit("A", Clearance(C.HEADING, 90)).safe)

    def test_conflict_between_prediction_samples_is_blocked(self):
        self.sim.reset(GameMode.SANDBOX)
        self.sim.spawn_aircraft(Aircraft("A", 125, 200, 90, 3000, 250,
                                           0, 3000, 250, AircraftState.AIRBORNE))
        self.sim.spawn_aircraft(Aircraft("B", 200, 125, 180, 3000, 250,
                                           180, 3000, 250, AircraftState.AIRBORNE))
        self.assertFalse(self.sim.transmit("A", Clearance(C.HEADING, 90)).safe)

    def test_speed_clearance_that_creates_conflict_is_blocked(self):
        self.sim.reset(GameMode.SANDBOX)
        self.sim.spawn_aircraft(Aircraft("A", 100, 200, 90, 3000, 30,
                                           90, 3000, 30, AircraftState.AIRBORNE))
        self.sim.spawn_aircraft(Aircraft("B", 350, 200, 270, 3000, 0,
                                           270, 3000, 0, AircraftState.AIRBORNE))
        self.assertFalse(self.sim.safety.conflicts(list(self.sim.aircraft.values())))
        self.assertFalse(self.sim.transmit("A", Clearance(C.SPEED, 250)).safe)

    def test_clearance_that_worsens_existing_conflict_is_blocked(self):
        self.sim.reset(GameMode.SANDBOX)
        self.sim.spawn_aircraft(Aircraft("A", 100, 200, 90, 3000, 100,
                                           90, 3000, 100, AircraftState.AIRBORNE))
        self.sim.spawn_aircraft(Aircraft("B", 400, 200, 270, 3000, 0,
                                           270, 3000, 0, AircraftState.AIRBORNE))
        self.assertTrue(self.sim.safety.conflicts(list(self.sim.aircraft.values())))
        self.assertFalse(self.sim.transmit("A", Clearance(C.SPEED, 250)).safe)

    def test_aircraft_spawn_is_silent(self):
        with self.assertNoLogs(level="INFO"):
            self.assertTrue(self.sim.spawn_aircraft(Aircraft("ACADEMY 02", 100, 100)))

    def test_configurable_safety_thresholds(self):
        self.sim.reset(GameMode.SANDBOX)
        first = Aircraft("A", 100, 200, 0, 3000, 0, 0, 3000, 0, AircraftState.AIRBORNE)
        second = Aircraft("B", 160, 200, 0, 3000, 0, 0, 3000, 0, AircraftState.AIRBORNE)
        traffic = [first, second]
        conflict = self.sim.safety.conflicts(traffic, predict=False)
        self.assertTrue(conflict)
        self.assertFalse(conflict[0].critical)
        self.sim.safety.set_thresholds(50, 25, 1000)
        self.assertFalse(self.sim.safety.conflicts(traffic, predict=False))
        self.sim.safety.set_thresholds(100, 70, 1000)
        self.assertTrue(self.sim.safety.conflicts(traffic, predict=False)[0].critical)
        with self.assertRaises(ValueError):
            self.sim.safety.set_thresholds(40, 80, 1000)
        self.sim.reset(GameMode.LESSON)
        self.assertEqual(self.sim.safety.horizontal_warning, 80)


if __name__ == "__main__":
    unittest.main()
