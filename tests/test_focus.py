"""Window focus regressions without requiring a desktop display."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from game.constants import GameMode
from game.game_state import GameState
from ui.main_window import MainWindow


class FocusTests(unittest.TestCase):
    def make_window(self, mode):
        window = MainWindow.__new__(MainWindow)
        window.root = Mock()
        window.root.tk.call.return_value = ""
        window.game = GameState()
        window.simulation = window.game.simulation
        window.simulation.reset(mode)
        window.lessons = Mock(current=None)
        window.story_manager = Mock(current=None)
        window.refresh = Mock()
        window.last_tick = 10.0
        return window

    def test_background_stops_all_gameplay_and_keeps_clock_current(self):
        for mode in (GameMode.LESSON, GameMode.STORY, GameMode.SANDBOX):
            with self.subTest(mode=mode):
                window = self.make_window(mode)
                window.lessons.current = Mock()
                window.story_manager.current = Mock()
                with patch("ui.main_window.time.monotonic", return_value=100.0), \
                        patch.object(window.simulation, "update") as update:
                    window.tick()
                self.assertTrue(window.simulation.paused)
                update.assert_not_called()
                window.lessons.current.update.assert_not_called()
                window.story_manager.current.update.assert_not_called()
                self.assertEqual(window.last_tick, 100.0)
                window.refresh.assert_called_once()
                window.root.after.assert_called_once_with(33, window.tick)

    def test_returning_to_game_requires_explicit_resume(self):
        window = self.make_window(GameMode.SANDBOX)
        window.tick()
        window.root.tk.call.return_value = ".toolbar.resume"
        window.tick()
        self.assertTrue(window.simulation.paused)
        window.simulation.resume()
        window.tick()
        self.assertFalse(window.simulation.paused)

    def test_internal_focus_including_native_popups_does_not_pause(self):
        for path in (".", ".controls.entry", ".combo.popdown.f.l"):
            with self.subTest(path=path):
                window = self.make_window(GameMode.SANDBOX)
                window.root.tk.call.return_value = path
                window.tick()
                self.assertFalse(window.simulation.paused)

    def test_menu_does_not_get_paused(self):
        window = self.make_window(GameMode.MAIN_MENU)
        window.tick()
        self.assertFalse(window.simulation.paused)

    def test_top_row_digit_shortcut_with_num_lock_mod1_state(self):
        window = self.make_window(GameMode.SANDBOX)
        window.simulation.aircraft = {"ONE": Mock(), "TWO": Mock()}
        window.select_aircraft = Mock()
        event = SimpleNamespace(keysym="KP_2", char="", keycode=0x32,
                                state=0x0008, widget=Mock())

        windows_sys = SimpleNamespace(platform="win32")
        windows_ctypes = SimpleNamespace(
            windll=SimpleNamespace(user32=SimpleNamespace(GetKeyState=Mock(return_value=0)))
        )
        with patch("ui.main_window.sys", windows_sys), patch("ui.main_window.ctypes", windows_ctypes):
            self.assertEqual(window._select_aircraft_with_key(event), "break")
        window.select_aircraft.assert_called_once_with("TWO")

    def test_tab_does_not_move_focus_when_there_are_no_aircraft(self):
        window = self.make_window(GameMode.SANDBOX)
        window.select_aircraft = Mock()
        event = SimpleNamespace(keysym="Tab", char="", keycode=9,
                                state=0, widget=Mock())

        self.assertEqual(window._select_aircraft_with_key(event), "break")
        window.select_aircraft.assert_not_called()

    def test_story_shortcut_does_not_share_simulation_menu_mnemonic(self):
        import tkinter as tk
        root = tk.Tk()
        try:
            with patch("ui.main_window.default_progress_path", return_value=None):
                window = MainWindow(root)
            self.assertEqual(window.menu_bar.entrycget(2, "label"), "Simulation")
            self.assertEqual(window.menu_bar.entrycget(2, "underline"), 1)
            self.assertTrue(root.bind("<Alt-s>"))
        finally:
            root.destroy()

    def test_display_commands_ignore_destroyed_game_screen_from_main_menu(self):
        window = self.make_window(GameMode.MAIN_MENU)
        window.radar = Mock()
        window.teletext_enabled = Mock()
        window.dos_enabled = Mock()
        window.teletext_page = Mock()
        window.teletext_pages = ("P100 Radar", "P101 Traffic", "P102 Runway", "P103 Alerts")

        window._set_display_mode("teletext")
        window._select_teletext_page(103)

        window.radar.winfo_exists.assert_not_called()
        window.teletext_enabled.set.assert_not_called()
        window.teletext_page.set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
