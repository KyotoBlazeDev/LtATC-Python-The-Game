"""Window focus regressions without requiring a desktop display."""
import unittest
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
