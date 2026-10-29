import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_version import VERSION, current_version
from release_config import resolve_release


class AppVersionTests(unittest.TestCase):
    def test_source_beta_is_valid_for_artifact_only_dispatch(self):
        self.assertEqual(current_version(), VERSION)
        resolved = resolve_release("workflow_dispatch", "branch", "main", VERSION)
        self.assertEqual(resolved, {"tag": VERSION, "publish": "false", "create_tag": "false"})

    def test_frozen_version_uses_requested_build_tag(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "build-info.json").write_text(
                json.dumps({"version": "v0.0.0-preview.42"}), encoding="utf-8")
            with patch("sys.frozen", True, create=True), patch("sys._MEIPASS", directory, create=True):
                self.assertEqual(current_version(), "v0.0.0-preview.42")
