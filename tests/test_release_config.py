import unittest

from release_config import resolve_release


class ReleaseConfigTests(unittest.TestCase):
    def test_manual_main_defaults_to_preview(self):
        self.assertEqual(resolve_release("workflow_dispatch", "branch", "main", run_number="7"),
                         {"tag": "v0.0.0-preview.7", "publish": "false", "create_tag": "false"})

    def test_manual_draft_requires_explicit_version(self):
        with self.assertRaises(ValueError):
            resolve_release("workflow_dispatch", "branch", "main", publish=True)
        self.assertEqual(resolve_release("workflow_dispatch", "branch", "main", "v0.9.0-beta-4", True),
                         {"tag": "v0.9.0-beta-4", "publish": "true", "create_tag": "true"})

    def test_existing_tag_formats_and_push_release(self):
        for version in ("v1.0.0", "v0.9.0-beta-3", "v0.9.0-beta.4", "v1.0.0-rc.1"):
            with self.subTest(version=version):
                self.assertEqual(resolve_release("push", "tag", version),
                                 {"tag": version, "publish": "true", "create_tag": "false"})

    def test_tag_dispatch_and_version_mismatch(self):
        self.assertEqual(resolve_release("workflow_dispatch", "tag", "v1.0.0", publish=True)["create_tag"], "false")
        with self.assertRaises(ValueError):
            resolve_release("workflow_dispatch", "tag", "v1.0.0", "v2.0.0", True)

    def test_invalid_versions_and_events(self):
        for version in ("main", "v1", "v1.0.0/branch", "v1.0.0;echo", "v1.0.0-beta"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                resolve_release("workflow_dispatch", "branch", "main", version)
        with self.assertRaises(ValueError):
            resolve_release("push", "branch", "main")
