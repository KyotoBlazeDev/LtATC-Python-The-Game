"""Touch selection and controls using Tk's synthesized pointer events."""
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ui.main_window import MainWindow
from ui.radar_canvas import RadarCanvas
from ui.touch import touch_pixels, size_touch_control, TouchScroller
from game.clearances import ClearanceType


class TouchTests(unittest.TestCase):
    def test_nested_traffic_drag_does_not_move_outer_sidebar(self):
        root = tk.Tk()
        try:
            outer = tk.Canvas(root, height=250)
            outer.pack()
            content = tk.Frame(outer)
            outer.create_window(0, 0, window=content, anchor="nw")
            inner = tk.Canvas(content, height=100)
            inner.pack()
            rows = tk.Frame(inner)
            inner.create_window(0, 0, window=rows, anchor="nw")
            label = tk.Label(rows, text="Traffic\n" * 50)
            label.pack()
            tk.Label(content, text="Settings\n" * 50).pack()
            root.update()
            for canvas in (inner, outer):
                canvas.configure(scrollregion=canvas.bbox("all"))
            scroller = TouchScroller(root, lambda: (outer, inner), lambda: True)
            scroller.attach(label)
            before = outer.yview()
            label.event_generate("<ButtonPress-1>", x=5, y=50)
            label.event_generate("<B1-Motion>", x=5, y=0)
            label.event_generate("<ButtonRelease-1>", x=5, y=0)
            self.assertGreater(inner.yview()[0], 0)
            self.assertEqual(outer.yview(), before)
        finally:
            root.destroy()

    def test_drag_over_button_scrolls_without_invoking_and_tap_still_works(self):
        root = tk.Tk()
        try:
            root.geometry("300x240")
            canvas = tk.Canvas(root)
            canvas.pack(fill="both", expand=True)
            rows = tk.Frame(canvas)
            canvas.create_window(0, 0, window=rows, anchor="nw")
            invoked = Mock()
            buttons = []
            for i in range(20):
                button = tk.Button(rows, text=f"Action {i}", command=invoked, pady=12)
                button.pack(fill="x")
                buttons.append(button)
            root.update()
            canvas.configure(scrollregion=canvas.bbox("all"))
            enabled = [True]
            scroller = TouchScroller(root, lambda: (canvas,), lambda: enabled[0])
            for button in buttons:
                scroller.attach(button)
            button = buttons[2]
            button.event_generate("<ButtonPress-1>", x=10, y=10)
            button.event_generate("<B1-Motion>", x=10, y=-100)
            button.event_generate("<ButtonRelease-1>", x=10, y=-100)
            root.update()
            self.assertGreater(canvas.yview()[0], 0)
            invoked.assert_not_called()
            canvas.yview_moveto(0)
            root.update()
            button = buttons[0]
            button.event_generate("<ButtonPress-1>", x=10, y=10)
            button.event_generate("<ButtonRelease-1>", x=10, y=10)
            invoked.assert_called_once()
            before = canvas.yview()
            enabled[0] = False
            button.event_generate("<ButtonPress-1>", x=10, y=10)
            button.event_generate("<B1-Motion>", x=10, y=-100)
            button.event_generate("<ButtonRelease-1>", x=10, y=-100)
            self.assertEqual(canvas.yview(), before)
        finally:
            root.destroy()

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
            # Exercise the real bindtags on a label inside the embedded window,
            # rather than calling a scroll method directly.
            source = window.lesson_panel.title_label
            source.event_generate("<ButtonPress-1>", x=5, y=5)
            source.event_generate("<B1-Motion>", x=5, y=-10000)
            source.event_generate("<ButtonRelease-1>", x=5, y=-10000)
            root.update()
            self.assertAlmostEqual(window.sidebar_canvas.yview()[1], 1.0, places=2)
            self.assertGreater(window.sidebar_canvas.yview()[0], 0)
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

