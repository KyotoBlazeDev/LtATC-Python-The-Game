"""Reusable chapter contract and checkpoint snapshots."""
from copy import deepcopy
from game.events import EventType, GameEvent

class StoryChapter:
    chapter_id = ""
    title = ""
    introduction: tuple[tuple[str, str], ...] = ()

    def __init__(self) -> None:
        self.objective = ""
        self.event_indicator = ""
        self.completed = False
        self.selected: set[str] = set()
        self.messages: list[tuple[str, str]] = []
        self._checkpoint = None
        self.checkpoint_name = "Start of chapter"

    def start(self, simulation, story_state) -> None:
        raise NotImplementedError

    def update(self, simulation, story_state, dt: float) -> None:
        pass

    def handle_clearance(self, aircraft, clearance) -> None:
        pass

    def validate_clearance(self, aircraft, clearance, simulation) -> str | None:
        """Return a story-specific reason to withhold a proposed transmission."""
        return None

    def available_actions(self) -> tuple[tuple[str, str], ...]:
        return ()

    def choose(self, action: str, simulation, story_state) -> None:
        pass

    def handle_event(self, event: GameEvent) -> None:
        if event.kind == EventType.AIRCRAFT_SELECTED and event.callsign:
            self.selected.add(event.callsign)

    def check_completion(self) -> bool:
        return self.completed

    def save_checkpoint(self, simulation, name: str, story_state=None) -> None:
        self.checkpoint_name = name
        state = {key: value for key, value in self.__dict__.items() if key != "_checkpoint"}
        self._checkpoint = (deepcopy(simulation.aircraft), deepcopy(simulation.runway),
                            simulation.selected_callsign, deepcopy(simulation.metrics),
                            deepcopy(state), deepcopy(story_state.__dict__) if story_state is not None else None)

    def retry_checkpoint(self, simulation, story_state=None) -> None:
        if self._checkpoint is None:
            return
        aircraft, runway, selected, metrics, state, persistent_state = self._checkpoint
        simulation.aircraft = deepcopy(aircraft)
        simulation.runway = deepcopy(runway)
        simulation.metrics = deepcopy(metrics)
        for key in tuple(self.__dict__):
            if key != "_checkpoint":
                del self.__dict__[key]
        self.__dict__.update(deepcopy(state))
        if story_state is not None and persistent_state is not None:
            story_state.__dict__.clear()
            story_state.__dict__.update(deepcopy(persistent_state))
        simulation.select(selected)
        simulation.resume()

    def say(self, speaker: str, message: str) -> None:
        self.messages.append((speaker, message))

    def drain_messages(self) -> list[tuple[str, str]]:
        result, self.messages = self.messages, []
        return result
