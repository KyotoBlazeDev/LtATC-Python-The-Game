# Beta 6 local validation — October 29, 2026

Prepared against clean `main` at `11b12d452f04ada55a95b85b25e5677ddd154442`.
Latest published release verified through GitHub: `v0.9.0-beta-5`, October 14,
2026, tag commit `a3fe82b0f9825d58c04387e912b124790072bcbd`.
See RELEASE_NOTES.md for the scope comparison.

## Results

- Windows x64, Python 3.12.14, Tcl/Tk 8.6.12.
- `python -m unittest discover -s tests -q`: 81 tests passed.
- Release workflow compileall command passed, including version and release modules.
- Release YAML and its embedded Python parsed; test/build dependencies and the
  draft publication gate were checked. Manual artifact-only version resolution
  is covered by tests.
- The workflow's actual packaging command,
  `python scripts/build_portable.py v0.9.0-beta-6`, completed successfully.
- PyInstaller 6.22.3, hooks 2026.8, Pillow 12.3.0. Local `.release-tools` had a
  Python 3.14 Pillow binary; the successful run used the matching Python 3.12
  Pillow from the bundled runtime, ahead of `.release-tools` on PYTHONPATH.
- Extracted assets matched source SHA-256 hashes, including the remastered plane.
  PyInstaller successfully converted and embedded its executable icon.
- Extracted executable smoke report: `ok: true`, version `v0.9.0-beta-6`,
  18 images, 25 animation frames, 72 plane headings. Menu, Sandbox, flight strip,
  scenario round trip, DOS and Teletext checks passed using isolated local state.
- ZIP size: 19,844,536 bytes. SHA-256:
  `1ad4e8d2bdae6546ee769ae85a488fe20ba06435ba82b1cbf01fc9ed25a106b1`.
  The emitted checksum file was independently checked with Get-FileHash.
- `git diff --check` passed.

Outputs and logs are in ignored `artifacts/`: the Beta 6 ZIP, checksum and smoke
report, plus `beta6-build.log` and `beta6-tests.log`.

## Limits

The hosted GitHub Actions matrix (Linux/Windows, Python 3.11–3.13), artifact
upload, and draft creation were not executed. The local run verifies the actual
Windows packaging command, not an end-to-end hosted workflow run. No human
visual review or clean-machine install was performed. No commits, tags, pushes,
workflow dispatches, or release mutations were made.
