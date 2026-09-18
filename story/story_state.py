from dataclasses import dataclass, field

@dataclass
class StoryState:
    student_confidence: int = 50
    student_competence: int = 0
    student_trust: int = 50
    lessons_completed: set[str] = field(default_factory=set)
    mistakes_corrected: int = 0
    safety_interventions: int = 0
    blaze_trust: int = 50
    unsafe_clearances_prevented: int = 0
    chapters_completed: set[str] = field(default_factory=set)
    current_chapter: str | None = None
    current_checkpoint: str | None = None
    training_complete: bool = False
