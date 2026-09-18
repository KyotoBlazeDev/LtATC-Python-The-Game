from story.incident_chapters import JFK2023, Austin2023, Burbank2023, JFK2024
from game.constants import GameMode

CHAPTERS = (JFK2023, Austin2023, Burbank2023, JFK2024)

class StoryManager:
    def __init__(self, state):
        self.state = state
        self.current = None

    def unlocked(self, chapter_id):
        index = next((i for i, chapter in enumerate(CHAPTERS) if chapter.chapter_id == chapter_id), None)
        if index is None:
            raise ValueError(f"Unknown chapter {chapter_id}")
        return index == 0 or CHAPTERS[index - 1].chapter_id in self.state.chapters_completed

    def start(self, chapter_id, simulation):
        if not self.unlocked(chapter_id):
            raise ValueError("Chapter is locked")
        if self.current is not None and simulation.mode == GameMode.STORY:
            if self.current.chapter_id == chapter_id:
                return self.current
            raise RuntimeError("Exit the active chapter before starting another")
        chapter_class = next((item for item in CHAPTERS if item.chapter_id == chapter_id), None)
        if chapter_class is None:
            raise ValueError(f"Unknown chapter {chapter_id}")
        self.current = chapter_class()
        self.state.current_chapter = chapter_id
        self.current.start(simulation, self.state)
        self.state.current_checkpoint = self.current.checkpoint_name
        return self.current
