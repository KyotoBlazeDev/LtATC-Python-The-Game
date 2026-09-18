from game.aircraft import Aircraft, AircraftState
from lessons.lesson_base import LessonBase

class HeadingLesson(LessonBase):
    lesson_id = "02"
    title = "Lesson 2: Heading Control"
    objectives = ("Select ACADEMY 01", "Command heading 180", "Verify the turn")
    introduction = (("Blaze", "A heading is a direction, not an instant turn. Select ACADEMY 01 and assign 180."),)

    def start(self, simulation) -> None:
        simulation.spawn_aircraft(Aircraft("ACADEMY 01", 420, 300, heading=270, altitude=3000, speed=100,
                                           target_heading=270, target_altitude=3000, target_speed=100, state=AircraftState.AIRBORNE))

    def check_completion(self, simulation) -> bool:
        plane = simulation.get_aircraft("ACADEMY 01")
        return bool(self.identified and plane and plane.target_heading == 180 and abs((plane.heading - 180 + 180) % 360 - 180) <= 5)
