import unittest
from unittest.mock import patch
from game.game_state import GameState
from game.clearances import Clearance, ClearanceType as C
from game.constants import AIRCRAFT_LIMIT, GameMode
from game.safety import Conflict


class ArrivalTrafficTests(unittest.TestCase):
    def test_speed_rate_change_and_inactive_modes(self):
        game = GameState()
        game.start_sandbox()
        game.simulation.aircraft.clear()
        manager = game.sandbox
        manager.traffic_rate = "High"
        game.simulation.set_speed(2)
        for _ in range(24):
            self.assertIsNone(manager.update(.1))
        self.assertIsNotNone(manager.update(.1))
        manager.traffic_rate = "Low"
        self.assertIsNone(manager.update(.1))
        self.assertAlmostEqual(manager._traffic_elapsed, .2)
        game.enter_menu()
        for _ in range(200):
            self.assertIsNone(manager.update(.1))
        self.assertEqual(game.simulation.mode, GameMode.MAIN_MENU)

    def test_blocked_spawn_is_skipped_without_backlog(self):
        game = GameState()
        game.start_sandbox()
        game.simulation.aircraft.clear()
        manager = game.sandbox
        manager.traffic_rate = "High"
        with patch.object(game.simulation.safety, "conflicts",
                          return_value=[Conflict("ACADEMY 02", "OTHER", 0, True)]):
            for _ in range(50):
                self.assertIsNone(manager.update(.1))
        self.assertEqual(len(game.simulation.aircraft), 0)
        self.assertIsNone(manager.update(.1))

    def test_traffic_rates_pause_and_manual(self):
        for rate, seconds in (("Low", 20), ("Medium", 10), ("High", 5)):
            game = GameState()
            game.start_sandbox()
            game.simulation.aircraft.clear()
            manager = game.sandbox
            manager.traffic_rate = rate
            for _ in range(seconds * 10 - 1):
                self.assertIsNone(manager.update(.1))
            game.simulation.pause()
            for _ in range(100):
                self.assertIsNone(manager.update(.1))
            game.simulation.resume()
            # Allow one extra tick for floating-point accumulation.
            spawned = manager.update(.1) or manager.update(.1)
            self.assertIsNotNone(spawned)
            self.assertFalse(game.simulation.safety.conflicts(list(game.simulation.aircraft.values())))
            manager.traffic_rate = "Manual"
            for _ in range(300):
                self.assertIsNone(manager.update(.1))

    def test_capacity_and_restart(self):
        game = GameState()
        game.start_sandbox()
        while len(game.simulation.aircraft) < AIRCRAFT_LIMIT:
            game.sandbox.spawn()
        game.sandbox.traffic_rate = "High"
        for _ in range(60):
            self.assertIsNone(game.sandbox.update(.1))
        game.start_sandbox(restart=True)
        self.assertEqual(game.sandbox.traffic_rate, "Manual")
        self.assertEqual(len(game.simulation.aircraft), 1)

    def test_arrival_requires_sequence_then_finishes(self):
        game = GameState()
        game.start_lesson("04")
        lesson, sim = game.lessons.current, game.simulation
        plane = sim.get_aircraft("ARRIVAL 04")
        lesson.identified = True
        self.assertIsNotNone(lesson.validate_clearance(plane, Clearance(C.LAND)))
        for kind in (C.APPROACH, C.GO_AROUND, C.APPROACH):
            clearance = Clearance(kind)
            self.assertIsNone(lesson.validate_clearance(plane, clearance))
            self.assertTrue(sim.transmit(plane.callsign, clearance).safe)
            lesson.handle_clearance(plane, clearance)
            sim.update(.1)
        self.assertIsNotNone(lesson.validate_clearance(plane, Clearance(C.LAND)))
        lesson.runway_checked = True
        sim.runway.closed = True
        self.assertFalse(sim.transmit(plane.callsign, Clearance(C.LAND)).safe)
        sim.runway.closed = False
        self.assertTrue(sim.transmit(plane.callsign, Clearance(C.LAND)).safe)
        lesson.handle_clearance(plane, Clearance(C.LAND))
        for _ in range(100):
            sim.update(.1)
            lesson.update(sim)
        self.assertTrue(lesson.completed)
        self.assertTrue(game.complete_lesson("04"))
        self.assertIn("04", game.story.lessons_completed)
        game.start_lesson("04", restart=True)
        self.assertEqual(game.lessons.current.stage, "approach")
