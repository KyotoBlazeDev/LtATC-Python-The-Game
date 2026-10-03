from game.aircraft import Aircraft, AircraftState
from game.clearances import ClearanceType
from lessons.lesson_base import LessonBase


class ArrivalLesson(LessonBase):
    lesson_id = "04"
    title = "Lesson 4: Arrival and Landing"
    introduction = (("Blaze", "{player}, select ARRIVAL 04 and clear an approach. Practice a go-around, then approach again. Check Runway 27 before landing."),)

    def __init__(self):
        super().__init__()
        self.stage = "approach"

    @property
    def objectives(self):
        instructions = {
            "approach": "Select ARRIVAL 04 and clear approach",
            "go_around": "Issue go-around to practice an interrupted arrival",
            "return": "Clear approach again when ready",
            "land": "Check Runway 27, then clear landing",
            "observe": "Observe touchdown and wait for the runway to clear",
        }
        return (instructions[self.stage],)

    def start(self, simulation):
        simulation.spawn_aircraft(Aircraft("ARRIVAL 04", 610, 360, heading=270,
            altitude=1500, speed=65, target_heading=270, target_altitude=1500,
            target_speed=65, state=AircraftState.AIRBORNE))

    def validate_clearance(self, aircraft, clearance):
        if aircraft is None or aircraft.callsign != "ARRIVAL 04":
            return "Select ARRIVAL 04 first."
        expected = {"approach": ClearanceType.APPROACH, "go_around": ClearanceType.GO_AROUND,
                    "return": ClearanceType.APPROACH, "land": ClearanceType.LAND}
        if self.stage == "observe" or clearance.clearance_type != expected[self.stage]:
            return "Follow the current lesson objective before transmitting."
        if self.stage == "land" and not self.runway_checked:
            return "Check Runway 27 before clearing the landing."
        return None

    def handle_clearance(self, aircraft, clearance):
        self.stage = {"approach": "go_around", "go_around": "return",
                      "return": "land", "land": "observe"}.get(self.stage, self.stage)
        if self.stage == "land":
            self.runway_checked = False

    def check_completion(self, simulation):
        plane = simulation.get_aircraft("ARRIVAL 04")
        return bool(self.stage == "observe" and self.identified and self.runway_checked
                    and plane and plane.state == AircraftState.PARKED
                    and simulation.runway.occupied_by is None)
