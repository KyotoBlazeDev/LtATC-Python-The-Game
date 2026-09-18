"""Versioned, failure-tolerant persistence for story and lesson progress."""
import json
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from story.story_state import StoryState

SAVE_VERSION = 1


def default_progress_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "LtATC" / "progress.json"


def load_progress(path: Path) -> StoryState:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("version") != SAVE_VERSION or not isinstance(payload.get("story"), dict):
            raise ValueError("Unsupported progress format")
        data = payload["story"]
        state = StoryState()
        for field in (
            "student_confidence", "student_competence", "student_trust",
            "mistakes_corrected", "safety_interventions", "blaze_trust",
            "unsafe_clearances_prevented",
        ):
            value = data.get(field, getattr(state, field))
            if isinstance(value, int) and not isinstance(value, bool):
                setattr(state, field, value)
        for field in ("lessons_completed", "chapters_completed"):
            value = data.get(field, [])
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                setattr(state, field, set(value))
        state.training_complete = bool(data.get("training_complete", False))
        return state
    except FileNotFoundError:
        return StoryState()
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        logging.warning("Progress file could not be loaded; starting with fresh progress", exc_info=True)
        return StoryState()


def save_progress(path: Path, state: StoryState) -> None:
    payload = {
        "version": SAVE_VERSION,
        "story": {
            "student_confidence": state.student_confidence,
            "student_competence": state.student_competence,
            "student_trust": state.student_trust,
            "lessons_completed": sorted(state.lessons_completed),
            "mistakes_corrected": state.mistakes_corrected,
            "safety_interventions": state.safety_interventions,
            "blaze_trust": state.blaze_trust,
            "unsafe_clearances_prevented": state.unsafe_clearances_prevented,
            "chapters_completed": sorted(state.chapters_completed),
            "training_complete": state.training_complete,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            temporary_name = temporary.name
            json.dump(payload, temporary, indent=2, sort_keys=True)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
