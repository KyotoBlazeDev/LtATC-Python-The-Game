from game.clearances import Clearance

class LessonBase:
    lesson_id = ""
    title = ""
    objectives: tuple[str, ...] = ()
    introduction: tuple[tuple[str, str], ...] = ()

    def __init__(self) -> None:
        self.completed = False
        self.identified = False
        self.runway_checked = False

    def start(self, simulation) -> None:
        raise NotImplementedError

    def update(self, simulation) -> None:
        self.completed = self.check_completion(simulation)

    def handle_clearance(self, aircraft, clearance: Clearance) -> None:
        pass

    def check_completion(self, simulation) -> bool:
        return False
