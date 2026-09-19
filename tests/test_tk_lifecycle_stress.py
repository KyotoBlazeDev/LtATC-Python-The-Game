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


if __name__ == "__main__":
    unittest.main()
