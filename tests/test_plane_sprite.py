import tkinter as tk
import unittest

from ui.plane_sprite import PlaneSprite


class PlaneSpriteTests(unittest.TestCase):
    def test_heading_rotation_transparency_and_cache(self):
        root = tk.Tk()
        root.withdraw()
        try:
            source = tk.PhotoImage(master=root, width=3, height=3)
            source.put("#ff0000", (1, 0))
            sprite = PlaneSprite(source)
            # North-facing nose rotates clockwise: north, east, south, west.
            for heading, position in ((0, (2, 1)), (90, (3, 2)),
                                      (180, (2, 3)), (270, (1, 2))):
                frame = sprite.at_heading(heading)
                self.assertEqual(frame.get(*position), (255, 0, 0))
                self.assertFalse(frame.transparency_get(*position))
                self.assertTrue(frame.transparency_get(0, 0))
            self.assertIs(sprite.at_heading(90), sprite.at_heading(450))
            self.assertIs(sprite.at_heading(90), sprite.at_heading(91))
            for angle in range(360):
                sprite.at_heading(angle)
            self.assertEqual(len(sprite.frames), 72)
        finally:
            root.destroy()
