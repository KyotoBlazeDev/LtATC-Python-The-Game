import json
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from unittest.mock import patch

from game.aircraft import AircraftState
from game.game_state import GameState
from game.clearances import Clearance, ClearanceType as C
from sandbox.persistence import load_scenario, save_scenario
from ui.main_window import MainWindow


class SandboxFeatureTests(unittest.TestCase):
    def setUp(self):
        self.game = GameState()
        self.game.start_sandbox()

    def test_priority_landing_and_closure_expire_only_when_running(self):
        manager = self.game.sandbox
        self.assertTrue(manager.trigger_emergency())
        plane = self.game.simulation.get_aircraft("ACADEMY 02")
        self.assertTrue(plane.emergency)
        plane.state, plane.altitude = AircraftState.PARKED, 0
        manager.update(.1)
        self.assertFalse(plane.emergency)
        self.assertTrue(manager.trigger_emergency())
        self.assertTrue(self.game.simulation.runway.closed)
        self.game.simulation.pause()
        for _ in range(200):
            manager.update(.1)
        self.assertTrue(self.game.simulation.runway.closed)
        self.game.simulation.resume()
        for _ in range(151):
            manager.update(.1)
        self.assertFalse(self.game.simulation.runway.closed)

    def test_challenge_escalates_counts_exits_and_finishes(self):
        manager = self.game.sandbox
        manager.start_challenge()
        self.game.simulation.get_aircraft("ACADEMY 02").x = 740
        manager.update(.1)
        self.assertEqual(manager.challenge_handled, 1)
        manager.challenge_elapsed = 59.9
        manager.update(.2)
        self.assertEqual(manager.traffic_rate, "Medium")
        manager.challenge_elapsed = 119.9
        manager.update(.2)
        self.assertEqual(manager.traffic_rate, "High")
        manager.challenge_elapsed = 179.9
        manager.update(.2)
        self.assertTrue(manager.challenge_finished)
        self.assertTrue(self.game.simulation.paused)
        self.assertIn("Score:", manager.challenge_report)
        self.game.simulation.resume()
        self.assertTrue(self.game.simulation.paused)
        self.assertIsNone(manager.spawn())
        self.assertFalse(self.game.simulation.transmit("ACADEMY 02", Clearance(C.HEADING, 90)).safe)

    def test_automatic_emergencies_and_bounded_trails(self):
        manager = self.game.sandbox
        manager.emergencies = True
        for _ in range(151):
            manager.update(.2)
        self.assertTrue(self.game.simulation.get_aircraft("ACADEMY 02").emergency)
        for _ in range(100):
            self.game.simulation.update(.2)
        self.assertEqual(len(self.game.simulation.trails["ACADEMY 02"]), 20)
        self.game.simulation.remove_aircraft("ACADEMY 02")
        self.assertNotIn("ACADEMY 02", self.game.simulation.trails)

    def test_round_trip_and_bad_load_preserve_session(self):
        sim = self.game.simulation
        sim.select("ACADEMY 02")
        sim.set_speed(2)
        self.game.sandbox.traffic_rate = "High"
        self.game.sandbox.trigger_emergency()
        self.game.sandbox.trigger_emergency()
        with TemporaryDirectory() as folder:
            path = Path(folder) / "scenario.json"
            save_scenario(path, self.game.sandbox)
            loaded = load_scenario(path)
            self.assertTrue(loaded.simulation.paused)
            self.assertEqual(loaded.simulation.speed, 2)
            self.assertEqual(loaded.simulation.selected_callsign, "ACADEMY 02")
            self.assertTrue(loaded.simulation.runway.closed)
            self.assertEqual(loaded._closure_remaining, 15)
            self.game.load_sandbox(path)
            self.assertIs(self.game.simulation, sim)
            original = path.read_text()
            for corrupt in ("[]", "{}", original.replace('"altitude": 3000', '"altitude": 3.5'),
                            original.replace('"speed": 90', '"speed": NaN')):
                path.write_text(corrupt)
                with self.assertRaises(ValueError):
                    self.game.load_sandbox(path)
                self.assertEqual(sim.selected_callsign, "ACADEMY 02")
                self.assertEqual(len(sim.aircraft), 1)


class FeatureSmokeTests(unittest.TestCase):
    def test_lesson_four_radar_and_save_load_menu(self):
        root = tk.Tk()
        try:
            with patch("ui.main_window.default_progress_path", return_value=None):
                window = MainWindow(root)
            window.show_lesson_menu()
            root.update()
            buttons = [child for child in self.descendants(window.frame)
                       if child.winfo_class() == "Button" and child.cget("text").startswith("Lesson 4")]
            self.assertEqual(len(buttons), 1)
            buttons[0].invoke()
            self.assertEqual(window.lessons.current.lesson_id, "04")
            window.select_aircraft("ARRIVAL 04")
            for kind in (C.APPROACH, C.GO_AROUND, C.APPROACH):
                window.issue_clearance(Clearance(kind))
            window.check_runway()
            window.issue_clearance(Clearance(C.LAND))
            for _ in range(100):
                window.simulation.update(.1)
                window.lessons.current.update(window.simulation)
            self.assertTrue(window.lessons.current.completed)
            window.start_sandbox()
            window.select_aircraft("ACADEMY 02")
            window.simulation.update(.2)
            window.simulation.update(.2)
            window.simulation.update(.2)
            window.refresh()
            self.assertTrue(window.radar.find_withtag("trail"))
            self.assertTrue(window.radar.find_withtag("heading_preview"))
            with TemporaryDirectory() as folder:
                path = str(Path(folder) / "scenario.json")
                with patch("ui.main_window.filedialog.asksaveasfilename", return_value=path):
                    window.save_sandbox()
                window.clear_all()
                with patch("ui.main_window.filedialog.askopenfilename", return_value=path):
                    window.load_sandbox()
                self.assertIn("ACADEMY 02", window.simulation.aircraft)
                self.assertTrue(window.simulation.paused)
                self.assertIs(window.sandbox.simulation, window.simulation)
                window.simulation_menu.invoke(1)
                self.assertFalse(window.simulation.paused)
                window.simulation_menu.invoke(0)
                self.assertTrue(window.simulation.paused)
            for mode in ("teletext", "dos", "radar"):
                window._set_display_mode(mode)
                window.refresh()
                root.update_idletasks()
            window.start_challenge()
            self.assertTrue(window.sandbox.challenge_active)
            window.clear_all()
            self.assertEqual(len(window.simulation.aircraft), 1)
            self.assertEqual(len(root.tk.call("after", "info")), 1)
        finally:
            root.destroy()

    def descendants(self, widget):
        for child in widget.winfo_children():
            yield child
            yield from self.descendants(child)
