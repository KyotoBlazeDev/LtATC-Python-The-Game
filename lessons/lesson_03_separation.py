from game.aircraft import Aircraft, AircraftState
from lessons.lesson_base import LessonBase

class SeparationLesson(LessonBase):
    lesson_id = "03"
    title = "Lesson 3: Keep Them Apart"
    objectives = ("Select a training aircraft", "Resolve the predicted conflict", "Maintain separation")
    introduction = (("Blaze", "Don't wait until the aircraft overlap. Look at where they're going."),)

    def __init__(self) -> None:
        super().__init__()
        self.resolution_issued = False

    def start(self, simulation) -> None:
        simulation.spawn_aircraft(Aircraft("EAGLE 21", 235, 280, heading=90, altitude=3000, speed=95,
                                           target_heading=90, target_altitude=3000, target_speed=95, state=AircraftState.AIRBORNE))
        simulation.spawn_aircraft(Aircraft("JET 404", 460, 280, heading=270, altitude=3000, speed=95,
                                           target_heading=270, target_altitude=3000, target_speed=95, state=AircraftState.AIRBORNE))

    def handle_clearance(self, aircraft, clearance) -> None:
        from game.clearances import ClearanceType
        if clearance.clearance_type in {ClearanceType.HEADING, ClearanceType.ALTITUDE}:
            self.resolution_issued = True

    def check_completion(self, simulation) -> bool:
        return self.resolution_issued and not simulation.safety.conflicts(list(simulation.aircraft.values()))
