"""Source version and the version stamped into a portable build."""
import json
import sys
from pathlib import Path

VERSION = "v0.9.0-beta-7"


def current_version():
    if getattr(sys, "frozen", False):
        return json.loads((Path(sys._MEIPASS) / "build-info.json").read_text(encoding="utf-8"))["version"]
    return VERSION
