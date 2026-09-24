"""Stress checks for Tk callbacks, bindings, and embedded display modes."""

import tkinter as tk
import unittest
from unittest.mock import patch

from ui.main_window import MainWindow


class TkLifecycleStressTests(unittest.TestCase):
    def make_window(self):
        root = tk.Tk()
        root.geometry("1100x700+0+0")
        with patch("ui.main_window.default_progress_path", return_value=None):
            window = MainWindow(root)
        window.start_sandbox()
        root.update()
        return root, window

    def close_window(self, root):
        if not root.winfo_exists():
            return
        for callback in root.tk.call("after", "info"):
            root.after_cancel(callback)
        root.destroy()

    def test_display_spam_uses_one_tick_and_mutates_live_traffic_safely(self):
        root, window = self.make_window()
        try:
            self.assertEqual(len(root.tk.call("after", "info")), 1)
            for cycle in range(10):
                for page in (100, 101, 102, 103):
                    window._select_teletext_page(page)
                    self.assertTrue(window.radar.teletext)
                    self.assertFalse(window.radar.dos)
                    window.refresh()

                window._set_display_mode("dos")
                self.assertTrue(window.radar.dos)
                self.assertFalse(window.radar.teletext)
                for command in ("STATUS", "DIR", "SELECT ACADEMY 02"):
                    window.dos_entry.insert(0, command)
                    window._run_dos_command()

                if cycle == 4:
                    window.simulation.remove_aircraft("ACADEMY 02")
                    window.refresh()
                    self.assertIsNone(window.simulation.selected_callsign)

                window._set_display_mode("radar")
                self.assertFalse(window.radar.dos)
                self.assertFalse(window.radar.teletext)
                root.update()

            self.assertEqual(len(root.tk.call("after", "info")), 1)
            self.assertTrue(window.radar.winfo_exists())
        finally:
            self.close_window(root)

    def test_revisiting_main_menu_does_not_duplicate_shortcut_bindings(self):
        root, window = self.make_window()
        try:
            baseline = {sequence: root.bind(sequence)
                        for sequence in ("<Alt-s>", "<Alt-l>", "<Alt-b>")}
            for _ in range(20):
                window.show_menu()
            current = {sequence: root.bind(sequence)
                       for sequence in ("<Alt-s>", "<Alt-l>", "<Alt-b>")}
            self.assertEqual(current, baseline)
        finally:
            self.close_window(root)

    def test_destroy_with_pending_tick_exits_without_delayed_callback(self):
        root, _window = self.make_window()
        self.assertEqual(len(root.tk.call("after", "info")), 1)
        root.destroy()

    def test_focus_loss_pauses_and_restore_does_not_resume(self):
        root, window = self.make_window()
        try:
            window.simulation.resume()
            root.withdraw()
            window.tick()
            self.assertTrue(window.simulation.paused)
            self.assertEqual(len(root.tk.call("after", "info")), 1)
            root.deiconify()
            root.update()
            self.assertTrue(window.simulation.paused)
        finally:
            self.close_window(root)

    def test_footer_boundaries_and_dos_focus_survive_view_switch(self):
        root, window = self.make_window()
        try:
            window._set_display_mode("teletext")
            root.update_idletasks()
            width, height = window.radar.winfo_width(), window.radar.winfo_height()
            for index in range(4):
                for x in (int(width * index / 4), min(width - 1, int(width * (index + 1) / 4) - 1)):
                    window.radar._click(type("Click", (), {"x": x, "y": height - 1})())
                    self.assertEqual(window.radar.teletext_page, 100 + index)
            window._set_display_mode("dos")
            window.dos_entry.focus_set()
            window.dos_entry.insert(0, "STATUS")
            window._show_radar_display()
            window.show_menu()
            window.start_sandbox()
            window._select_teletext_page(103)
            self.assertEqual(window.radar.teletext_page, 103)
        finally:
            self.close_window(root)

    def test_status_color_covers_active_paused_warning_and_critical(self):
        root, window = self.make_window()
        try:
            class Conflict:
                def __init__(self, critical):
                    self.critical = critical
                    self.first = "ACADEMY 02"
                    self.second = "OTHER"

            states = []
            window.simulation.resume()
            window.refresh([])
            states.append(window.status_fields[-1].cget("text"))
            window.simulation.pause()
            window.refresh([])
            states.append(window.status_fields[-1].cget("text"))
            window.refresh([Conflict(False)])
            states.append(window.status_fields[-1].cget("text"))
            window.refresh([Conflict(True)])
            states.append(window.status_fields[-1].cget("text"))
            self.assertEqual(states, ["ACTIVE", "PAUSED", "WARNING", "CRITICAL"])
            self.assertNotEqual(window.status_fields[-1].cget("bg"), window.status_fields[0].cget("bg"))
        finally:
            self.close_window(root)


if __name__ == "__main__":
    unittest.main()
