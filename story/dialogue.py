from collections import deque
from dataclasses import dataclass
from typing import Callable

@dataclass
class DialogueLine:
    speaker: str
    message: str
    on_finish: Callable[[], None] | None = None

class DialogueQueue:
    def __init__(self) -> None:
        self.lines: deque[DialogueLine] = deque()
        self.current: DialogueLine | None = None

    def show(self, speaker: str, message: str, on_finish: Callable[[], None] | None = None) -> None:
        self.lines.append(DialogueLine(speaker, message, on_finish))
        if self.current is None:
            self.advance()

    def advance(self) -> DialogueLine | None:
        if self.current and self.current.on_finish:
            self.current.on_finish()
        self.current = self.lines.popleft() if self.lines else None
        return self.current

    def clear(self) -> None:
        self.lines.clear()
        self.current = None
