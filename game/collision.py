"""Swept collision checks in simplified game units, separate from separation alerts."""
from dataclasses import dataclass
from itertools import combinations
from math import sqrt


@dataclass(frozen=True)
class Collision:
    first: str
    second: str
    x: float
    y: float

    @property
    def reason(self):
        return f"Collision between {self.first} and {self.second}."


def find_collision(aircraft, previous):
    """Return the earliest overlap along this tick's linear movement segments.

    A collision means centers within 12 logical pixels and 100 feet vertically.
    Parked ground traffic is excluded. These are game rules, not ATC minima.
    """
    earliest = None
    for first, second in combinations(aircraft, 2):
        a0 = previous[first.callsign]
        b0 = previous[second.callsign]
        if max(a0[2], first.altitude) <= 0 or max(b0[2], second.altitude) <= 0:
            continue
        dx, dy, dz = (a0[i] - b0[i] for i in range(3))
        vx = first.x - second.x - dx
        vy = first.y - second.y - dy
        vz = first.altitude - second.altitude - dz
        lo, hi = 0.0, 1.0
        if vz:
            enter, leave = sorted(((-100 - dz) / vz, (100 - dz) / vz))
            lo, hi = max(lo, enter), min(hi, leave)
        elif abs(dz) > 100:
            continue
        aa, bb, cc = vx * vx + vy * vy, 2 * (dx * vx + dy * vy), dx * dx + dy * dy - 12 ** 2
        if aa:
            discriminant = bb * bb - 4 * aa * cc
            if discriminant < 0:
                continue
            root = sqrt(discriminant)
            lo, hi = max(lo, (-bb - root) / (2 * aa)), min(hi, (-bb + root) / (2 * aa))
        elif cc > 0:
            continue
        if lo > hi or (earliest is not None and lo >= earliest[0]):
            continue
        x = (a0[0] + b0[0] + lo * (first.x + second.x - a0[0] - b0[0])) / 2
        y = (a0[1] + b0[1] + lo * (first.y + second.y - a0[1] - b0[1])) / 2
        earliest = lo, Collision(first.callsign, second.callsign, x, y)
    return earliest
