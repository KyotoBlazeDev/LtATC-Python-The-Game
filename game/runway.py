from dataclasses import dataclass
import re

@dataclass
class Runway:
    name: str = "27"
    start_x: float = 420
    start_y: float = 360
    end_x: float = 190
    end_y: float = 360
    closed: bool = False
    arrival_enabled: bool = True
    departure_enabled: bool = True
    occupied_by: str | None = None

    @property
    def heading(self) -> int:
        """Return the schematic centerline heading encoded by the designator."""
        match = re.fullmatch(r"(0?[1-9]|[12]\d|3[0-6])[LRC]?", self.name.strip(), re.IGNORECASE)
        if match is None:
            raise ValueError(f"Invalid runway designator: {self.name!r}")
        number = int(match.group(1))
        if not 1 <= number <= 36:
            raise ValueError(f"Invalid runway designator: {self.name!r}")
        return (number * 10) % 360
