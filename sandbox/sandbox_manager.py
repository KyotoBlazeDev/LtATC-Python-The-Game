import random
from game.aircraft import Aircraft, AircraftState
from game.constants import AIRCRAFT_LIMIT

class SandboxManager:
    def __init__(self, simulation) -> None:
        self.simulation = simulation
        self.next_number = 2
        self.traffic_rate = "Manual"
        self.weather = "Clear"
        self.time_of_day = "Day"
        self.emergencies = False

    def spawn(self) -> Aircraft | None:
        if self.simulation.game_over or len(self.simulation.aircraft) >= AIRCRAFT_LIMIT:
            return None
        while f"ACADEMY {self.next_number:02d}" in self.simulation.aircraft:
            self.next_number += 1
        callsign = f"ACADEMY {self.next_number:02d}"
        self.next_number += 1
        heading = random.choice((45, 90, 135, 180, 225, 270, 315))
        altitude = random.choice((2000, 3000, 4000, 5000))
        speed = random.randrange(70, 121)
        plane = Aircraft(callsign, random.randrange(90, 610), random.randrange(85, 560), heading,
                         altitude, speed, heading, altitude, speed, AircraftState.AIRBORNE)
        self.simulation.spawn_aircraft(plane)
        return plane
