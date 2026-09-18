"""Collision, terminal-state, restart and real Tk rendering regressions."""
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from game.aircraft import Aircraft, AircraftState
from game.clearances import Clearance, ClearanceType
from game.constants import GameMode
from game.game_state import GameState
from game.simulation import Simulation
from ui.radar_canvas import RadarCanvas
from ui.main_window import MainWindow


def plane(name, x, altitude=3000, heading=90, speed=0):
    return Aircraft(name, x, 200, heading=heading, altitude=altitude, speed=speed,
                    target_heading=heading, target_altitude=altitude,
                    target_speed=speed, state=AircraftState.AIRBORNE)


def scene(mode=GameMode.SANDBOX, distance=8, altitude=3000):
    sim = Simulation()
    sim.reset(mode)
    sim.training_safety = False
    sim.spawn_aircraft(plane("A", 100))
    sim.spawn_aircraft(plane("B", 100 + distance, altitude))
    return sim


class GameOverTests(unittest.TestCase):
    def test_safety_toggle_controls_predicted_clearance_blocking(self):
        for kind in (ClearanceType.HEADING, ClearanceType.ALTITUDE):
            sim = Simulation()
            sim.reset(GameMode.SANDBOX)
            if kind == ClearanceType.HEADING:
                sim.spawn_aircraft(plane("A", 100, heading=0, speed=100))
                sim.spawn_aircraft(plane("B", 300))
                value = 90
            else:
                sim.spawn_aircraft(plane("A", 100, altitude=5000))
                sim.spawn_aircraft(plane("B", 100))
                value = 3000
            clearance = Clearance(kind, value)
            self.assertFalse(sim.transmit("A", clearance).safe)
            sim.training_safety = False
            self.assertTrue(sim.transmit("A", clearance).safe)
            self.assertFalse(sim.transmit("A", Clearance(kind, -1)).safe)

    def test_collision_demo_runs_to_game_over_and_can_be_protected(self):
        for safety in (False, True):
            game = GameState()
            game.start_sandbox()
            game.start_sandbox(collision_demo=True)
            sim = game.simulation
            self.assertTrue(sim.paused)
            self.assertFalse(sim.training_safety)
            self.assertEqual(set(sim.aircraft), {"ACADEMY 02", "ACADEMY 03"})
            sim.training_safety = safety
            sim.resume()
            for _ in range(130):
                sim.update(1 / 30)
            self.assertTrue(sim.paused)
            self.assertEqual(sim.game_over, not safety)
            if not safety:
                self.assertAlmostEqual(sim.collision.x, 350)
                self.assertAlmostEqual(sim.collision.y, 250)
            game.start_sandbox(collision_demo=True)
            self.assertFalse(sim.game_over)
            self.assertEqual(len(sim.aircraft), 2)

    def test_collision_ends_interactive_modes_even_with_warnings_hidden(self):
        for mode in (GameMode.LESSON, GameMode.SANDBOX):
            sim = scene(mode)
            sim.separation_warnings = False
            sim.safety.set_thresholds(2, 1, 1)
            sim.update(.1)
            self.assertTrue(sim.game_over)
            self.assertTrue(sim.paused)
            self.assertEqual((sim.collision.x, sim.collision.y), (104, 200))

    def test_warning_or_vertical_separation_is_not_collision(self):
        for distance, altitude in ((30, 3000), (8, 3200)):
            sim = scene(distance=distance, altitude=altitude)
            sim.update(.1)
            self.assertFalse(sim.game_over)

    def test_training_safety_pauses_without_game_over(self):
        sim = scene(distance=30)
        sim.training_safety = True
        sim.update(.1)
        self.assertTrue(sim.paused)
        self.assertFalse(sim.game_over)

    def test_story_and_ground_overlap_do_not_create_crash(self):
        sim = scene(GameMode.STORY)
        sim.update(.1)
        self.assertFalse(sim.game_over)
        sim = scene(altitude=0)
        sim.update(.1)
        self.assertFalse(sim.game_over)

    def test_crossing_between_frames_is_detected_and_frozen_at_impact(self):
        sim = scene(distance=16)
        sim.aircraft["A"] = plane("A", 100, speed=250)
        sim.aircraft["B"] = plane("B", 116, heading=270, speed=250)
        sim.update(.2)  # Both end outside the collision radius after swapping sides.
        self.assertTrue(sim.game_over)
        self.assertAlmostEqual(sim.aircraft["B"].x - sim.aircraft["A"].x, 12)
        self.assertAlmostEqual(sim.collision.x, 108)

    def test_game_over_cannot_resume_mutate_traffic_or_transmit(self):
        sim = scene()
        sim.update(.1)
        collision = sim.collision
        before = [(p.x, p.y) for p in sim.aircraft.values()]
        sim.resume()
        sim.update(.2)
        self.assertTrue(sim.paused)
        self.assertEqual(before, [(p.x, p.y) for p in sim.aircraft.values()])
        self.assertIs(sim.collision, collision)
        self.assertFalse(sim.transmit("A", Clearance(ClearanceType.HEADING, 180)).safe)
        self.assertFalse(sim.spawn_aircraft(plane("C", 400)))
        sim.remove_aircraft("A")
        self.assertIn("A", sim.aircraft)

    def test_restart_clears_failure_and_does_not_award_completion(self):
        game = GameState()
        game.start_lesson("03")
        sim = game.simulation
        sim.aircraft = scene().aircraft
        sim.training_safety = False
        sim.update(.1)
        self.assertFalse(game.complete_lesson("03"))
        self.assertFalse(game.story.lessons_completed)
        game.start_lesson("03", restart=True)
        self.assertFalse(sim.game_over)
        game.enter_menu()
        game.start_sandbox()
        sim.aircraft = scene().aircraft
        sim.training_safety = False
        sim.update(.1)
        self.assertTrue(game.start_sandbox(restart=True))
        self.assertFalse(sim.game_over)
        self.assertFalse(sim.paused)
        self.assertTrue(sim.training_safety)
        self.assertEqual(set(sim.aircraft), {"ACADEMY 02"})

    def test_tick_skips_lesson_completion_after_collision(self):
        window = MainWindow.__new__(MainWindow)
        window.root = Mock()
        window.root.tk.call.return_value = "."
        window.simulation = scene(GameMode.LESSON)
        window.lessons = Mock()
        window.story_manager = Mock()
        window.refresh = Mock()
        window.last_tick = 0
        window.tick()
        window.lessons.current.update.assert_not_called()
        window.refresh.assert_called_once()
        window.root.after.assert_called_once_with(33, window.tick)


class GameOverRenderingTests(unittest.TestCase):
    def test_window_failure_panel_retry_and_main_menu(self):
        root = tk.Tk()
        root.withdraw()
        try:
            with patch("ui.main_window.default_progress_path", return_value=None):
                window = MainWindow(root)
            window.start_sandbox()
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            next(w for w in descendants(window.frame)
                 if w.winfo_class() == "Button" and w.cget("text") == "Collision demo").invoke()
            self.assertTrue(window.simulation.paused)
            self.assertFalse(window.simulation.training_safety)
            self.assertEqual(len(window.simulation.aircraft), 2)
            window.simulation.aircraft = scene().aircraft
            window.simulation.training_safety = False
            window.simulation.resume()
            window.simulation.update(.1)
            window.refresh()
            self.assertEqual(window.game_over_panel.winfo_manager(), "pack")
            self.assertIn("Collision between A and B", window.game_over_reason.cget("text"))
            buttons = {w.cget("text"): w for w in window.game_over_panel.winfo_children()
                       if w.winfo_class() == "Button"}
            buttons["Retry"].invoke()
            self.assertFalse(window.simulation.game_over)
            self.assertEqual(set(window.simulation.aircraft), {"ACADEMY 02"})
            self.assertFalse(window.game_over_panel.winfo_manager())
            window.simulation.aircraft = scene().aircraft
            window.simulation.training_safety = False
            window.simulation.update(.1)
            window.refresh()
            next(w for w in window.game_over_panel.winfo_children()
                 if w.winfo_class() == "Button" and w.cget("text") == "Main menu").invoke()
            self.assertEqual(window.simulation.mode, GameMode.MAIN_MENU)
            self.assertFalse(window.simulation.game_over)
        finally:
            for callback in root.tk.call("after", "info"):
                root.after_cancel(callback)
            root.destroy()

    def test_asset_and_fallback_render_in_all_display_modes(self):
        root = tk.Tk()
        root.withdraw()
        try:
            path = Path(__file__).resolve().parents[1] / "assets" / "boom_explosion.png"
            image = tk.PhotoImage(master=root, file=str(path)).subsample(6)
            radar = RadarCanvas(root, lambda _: None, explosion_image=image)
            sim = scene()
            sim.update(.1)
            radar.refresh(sim)
            self.assertEqual(radar.type(radar.find_withtag("collision")[0]), "image")
            radar.explosion_image = None
            radar.refresh(sim)
            self.assertEqual(radar.type(radar.find_withtag("collision")[0]), "text")
            for display in (radar.set_teletext, radar.set_dos):
                display(True)
                radar.refresh(sim)
                self.assertTrue(radar.find_withtag("game_over"))
            sim.reset(GameMode.SANDBOX)
            radar.refresh(sim)
            self.assertFalse(radar.find_withtag("game_over"))
        finally:
            root.destroy()
