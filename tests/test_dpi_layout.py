"""High-DPI layout checks for the fixed-size main application window."""

import tkinter as tk
import tkinter.font as tkfont
import unittest
from unittest.mock import patch

from ui.main_window import INCIDENT_CONTENT_WARNING, MainWindow


SCALE_PERCENTAGES = (100, 125, 150, 175)


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class DpiLayoutTests(unittest.TestCase):
    def make_window(self, percentage):
        root = tk.Tk()
        root.tk.call("tk", "scaling", 96 * percentage / 100 / 72)
        root.geometry("1100x700+0+0")
        with patch("ui.main_window.default_progress_path", return_value=None):
            window = MainWindow(root)
        window._cancel_startup()
        return root, window

    def close_window(self, root):
        for callback in root.tk.call("after", "info"):
            root.after_cancel(callback)
        root.destroy()

    def assert_widget_inside_root(self, root, widget, percentage):
        right = widget.winfo_rootx() - root.winfo_rootx() + widget.winfo_width()
        bottom = widget.winfo_rooty() - root.winfo_rooty() + widget.winfo_height()
        self.assertLessEqual(right, root.winfo_width(), f"{percentage}%: {widget} clipped horizontally")
        self.assertLessEqual(bottom, root.winfo_height(), f"{percentage}%: {widget} clipped vertically")

    def test_story_menu_and_status_bar_fit_supported_scaling(self):
        for percentage in SCALE_PERCENTAGES:
            with self.subTest(percentage=percentage):
                root, window = self.make_window(percentage)
                try:
                    window.show_story_menu()
                    root.update()
                    widgets = tuple(descendants(window.frame))
                    warning = next(widget for widget in widgets
                                   if widget.winfo_class() == "Label"
                                   and widget.cget("text") == INCIDENT_CONTENT_WARNING)
                    buttons = tuple(widget for widget in widgets if widget.winfo_class() == "Button")
                    self.assertEqual(len([button for button in buttons
                                          if button.cget("text").startswith("Case ")]), 4)
                    for widget in (warning, *buttons):
                        self.assert_widget_inside_root(root, widget, percentage)
                    self.assertGreaterEqual(warning.winfo_height(), warning.winfo_reqheight())
                    for button in buttons:
                        font = tkfont.Font(root=root, font=button.cget("font"))
                        self.assertLessEqual(font.measure(button.cget("text")) + 24,
                                             button.winfo_width(),
                                             f"{percentage}%: button text clipped: {button.cget('text')!r}")

                    menu_font = tkfont.nametofont("TkMenuFont", root=root)
                    menu_width = sum(menu_font.measure(window.menu_bar.entrycget(index, "label")) + 24
                                     for index in range(window.menu_bar.index("end") + 1))
                    self.assertLessEqual(menu_width, root.winfo_width(),
                                         f"{percentage}%: application menu bar clipped")

                    window.start_sandbox()
                    root.update()
                    previous_right = 0
                    for field in window.status_fields:
                        self.assert_widget_inside_root(root, field, percentage)
                        left = field.winfo_rootx() - root.winfo_rootx()
                        self.assertGreaterEqual(left, previous_right)
                        previous_right = left + field.winfo_width()
                        font = tkfont.Font(root=root, font=field.cget("font"))
                        self.assertLessEqual(font.measure(field.cget("text")) + 8,
                                             field.winfo_width(),
                                             f"{percentage}%: status text clipped: {field.cget('text')!r}")
                finally:
                    self.close_window(root)


if __name__ == "__main__":
    unittest.main()
