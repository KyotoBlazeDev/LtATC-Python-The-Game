import unittest
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import Mock, patch

from game.game_state import GameState
from ui.main_window import MainWindow


class DeleteAircraftTests(unittest.TestCase):
    def test_aircraft_shortcuts_work_while_classic_dropdown_has_focus(self):
        root = tk.Tk()
        try:
            with patch("ui.main_window.default_progress_path", return_value=None):
                window = MainWindow(root)
            for callback in root.tk.call("after", "info"):
                root.after_cancel(callback)
            window.start_sandbox()
            window.spawn_aircraft()
            root.update()

            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)

            dropdown = next(widget for widget in descendants(window.frame)
                            if widget.winfo_class() == "Menubutton")
            dropdown.focus_force()
            root.update()
            dropdown.event_generate("<KeyPress-2>")
            root.update()
            self.assertEqual(window.simulation.selected_callsign, "ACADEMY 03")
            dropdown.event_generate("<KeyPress-Tab>")
            root.update()
            self.assertEqual(window.simulation.selected_callsign, "ACADEMY 02")
        finally:
            for callback in root.tk.call("after", "info"):
                root.after_cancel(callback)
            root.destroy()

    def test_clicking_radar_after_editing_allows_real_delete_key(self):
        root = tk.Tk()
        try:
            with patch("ui.main_window.default_progress_path", return_value=None):
                window = MainWindow(root)
            for callback in root.tk.call("after", "info"):
                root.after_cancel(callback)
            window.start_sandbox()
            window.simulation.pause()
            entry = tk.Entry(window.frame)
            entry.pack()
            entry.insert(0, "keep text")
            root.update()
            entry.focus_force()
            root.update()
            window.refresh()
            x, y = window.radar.positions["ACADEMY 02"]
            window.radar.event_generate("<Button-1>", x=int(x), y=int(y))
            root.update()
            self.assertEqual(window.simulation.selected_callsign, "ACADEMY 02")
            with patch("ui.main_window.messagebox.askyesno", return_value=True) as dialog:
                root.focus_get().event_generate("<KeyPress-Delete>")
                root.update()
                dialog.assert_called_once()
            self.assertNotIn("ACADEMY 02", window.simulation.aircraft)
            self.assertEqual(entry.get(), "keep text")
        finally:
            root.destroy()

    def window(self):
        window = MainWindow.__new__(MainWindow)
        window.game = GameState()
        window.game.start_sandbox()
        window.simulation = window.game.simulation
        window.simulation.select("ACADEMY 02")
        window.root = Mock()
        window.refresh = Mock()
        return window

    def test_delete_key_confirms_and_cleans_selection_and_runway(self):
        window = self.window()
        window.simulation.runway.occupied_by = "ACADEMY 02"
        def confirm(*args, **kwargs):
            self.assertTrue(window.simulation.paused)
            self.assertIn("ACADEMY 02", args[1])
            self.assertEqual(kwargs["default"], "no")
            return True
        with patch("ui.main_window.messagebox.askyesno", side_effect=confirm) as dialog:
            result = window._select_aircraft_with_key(SimpleNamespace(keysym="Delete", state=0, widget=Mock()))
        self.assertEqual(result, "break")
        dialog.assert_called_once()
        self.assertFalse(window.simulation.aircraft)
        self.assertIsNone(window.simulation.selected_callsign)
        self.assertIsNone(window.simulation.runway.occupied_by)
        self.assertFalse(window.simulation.paused)

    def test_cancel_preserves_aircraft_and_pause_state(self):
        for paused in (False, True):
            window = self.window()
            window.simulation.paused = paused
            with patch("ui.main_window.messagebox.askyesno", return_value=False):
                window.remove_selected()
            self.assertIn("ACADEMY 02", window.simulation.aircraft)
            self.assertEqual(window.simulation.paused, paused)

    def test_no_selection_and_lesson_do_not_prompt(self):
        window = self.window()
        with patch("ui.main_window.messagebox.askyesno") as dialog:
            window.simulation.select(None)
            window.remove_selected()
            window.game.start_lesson("01")
            window.simulation.select("CARGO 90")
            window.remove_selected()
            dialog.assert_not_called()
