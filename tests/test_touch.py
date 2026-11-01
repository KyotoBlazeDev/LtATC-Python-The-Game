"""Touch selection and controls using Tk's synthesized pointer events."""
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ui.main_window import MainWindow
from ui.radar_canvas import RadarCanvas
from ui.touch import touch_pixels, size_touch_control
from game.clearances import ClearanceType


class TouchTests(unittest.TestCase):
    def test_scaled_targets_and_original_padding_restored(self):
        root = tk.Tk()
        try:
            for scaling in (96 / 72, 2, 7 / 3):
                root.tk.call("tk", "scaling", scaling)
                button = tk.Button(root, text="Go", padx=6, pady=2)
                original = (str(button.cget("padx")), str(button.cget("pady")))
                size_touch_control(button, True)
                self.assertGreaterEqual(button.winfo_reqheight(), touch_pixels(button))
                self.assertGreaterEqual(button.winfo_reqwidth(), touch_pixels(button))
                size_touch_control(button, False)
                self.assertEqual((str(button.cget("padx")), str(button.cget("pady"))), original)
                button.destroy()
        finally:
            root.destroy()

    def test_radar_selects_nearest_and_expands_only_in_touch_mode(self):
        root = tk.Tk()
        try:
            selected = Mock()
            radar = RadarCanvas(root, selected)
            radar.positions = {"NEAR": (50, 50), "FAR": (65, 50)}
            radar._click(SimpleNamespace(x=49, y=50))
            selected.assert_called_once_with("NEAR")
            selected.reset_mock()
            radar.positions = {"TARGET": (50, 50)}
            radar._click(SimpleNamespace(x=80, y=50))
            selected.assert_not_called()
            radar.touch_enabled = True
            radar._click(SimpleNamespace(x=80, y=50))
            selected.assert_called_once_with("TARGET")
        finally:
            root.destroy()

    def test_touch_toggle_dynamic_options_and_rebuild(self):
        root = tk.Tk()
        try:
            with patch("ui.main_window.default_progress_path", return_value=None):
                window = MainWindow(root)
            window._cancel_startup()
            window.start_sandbox()
            window.touch_enabled.set(True)
            window._apply_touch_controls()
            root.update()
            root.geometry("760x600")
            root.update()
            self.assertGreater(window.radar.winfo_height(), 200)
            self.assertGreater(window.radar.winfo_width(), 200)
            for button in window.touch_actions.winfo_children():
                self.assertGreaterEqual(button.winfo_height(), touch_pixels(button))
            self.assertTrue(window.touch_scroll.winfo_ismapped())
            self.assertTrue(window.aircraft_panel.touch_scroll.winfo_ismapped())
            window.controls._choose(ClearanceType.HEADING)
            for button in window.controls.options.winfo_children():
                self.assertGreaterEqual(button.winfo_reqheight(), touch_pixels(button))
            window._build_game()
            self.assertTrue(window.radar.touch_enabled)
            window.touch_enabled.set(False)
            window._apply_touch_controls()
            root.update()
            self.assertFalse(window.touch_scroll.winfo_ismapped())
            self.assertFalse(window.aircraft_panel.touch_scroll.winfo_ismapped())
        finally:
            for callback in root.tk.call("after", "info"):
                root.after_cancel(callback)
            root.destroy()

