from dataclasses import dataclass

@dataclass(frozen=True)
class Character:
    name: str
    role: str
    portrait: str | None = None

BLAZE = Character("Blaze", "Instructor", "BlazeFerrende_avatar_bust.png")
STUDENT01 = Character("Student01", "Trainee")
MERVYN = Character("Mervyn", "Original game mascot", "Mervyn.png")
TRAINER01 = Character("TRAINER01", "Training program")
