from game.aircraft import Aircraft, AircraftState
from lessons.lesson_base import LessonBase

class DepartureLesson(LessonBase):
    lesson_id = "01"
    title = "Lesson 1: The First Departure"
    objectives = ("Select CARGO 90", "Check Runway 27 status", "Clear CARGO 90 for takeoff", "Observe the departure")
    introduction = (("Blaze", "{player}, CARGO 90 is ready for your first departure."),
                    ("CARGO 90", "Tower, CARGO 90 ready for departure."),
                    ("Blaze", "Check the runway before issuing the clearance."))

    def start(self, simulation) -> None:
        simulation.spawn_aircraft(Aircraft("CARGO 90", 445, 360, state=AircraftState.HOLDING_SHORT))

    def check_completion(self, simulation) -> bool:
        plane = simulation.get_aircraft("CARGO 90")
        return bool(self.identified and self.runway_checked and plane and plane.state == AircraftState.AIRBORNE)
