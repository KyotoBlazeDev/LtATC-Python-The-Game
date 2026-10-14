"""Cached heading sprites using Tk only, preserving the portable runtime."""

from math import ceil, cos, hypot, radians, sin
import tkinter as tk


class PlaneSprite:
    """Rotate north-facing artwork clockwise in five-degree heading steps."""

    def __init__(self, source):
        self.source = source
        self.frames = {}
        self.size = ceil(hypot(source.width(), source.height()))
        self.pixels = [[None if source.transparency_get(x, y) else source.get(x, y)
                        for x in range(source.width())] for y in range(source.height())]

    def at_heading(self, heading):
        angle = (round(heading / 5) * 5) % 360
        if angle not in self.frames:
            frame = tk.PhotoImage(master=self.source.tk, width=self.size, height=self.size)
            c, s = cos(radians(angle)), sin(radians(angle))
            center = (self.size - 1) / 2
            for y in range(self.size):
                for x in range(self.size):
                    dx, dy = x - center, y - center
                    sx = round(c * dx + s * dy + (self.source.width() - 1) / 2)
                    sy = round(-s * dx + c * dy + (self.source.height() - 1) / 2)
                    if 0 <= sx < self.source.width() and 0 <= sy < self.source.height():
                        pixel = self.pixels[sy][sx]
                        if pixel is not None:
                            frame.put('#%02x%02x%02x' % pixel, (x, y))
            self.frames[angle] = frame
        return self.frames[angle]
