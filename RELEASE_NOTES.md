# LtATC v0.9.0-beta-6 — prepared, unpublished

This beta improves portable release verification and version identification.

- The window title and `--version` identify the running version. Portable builds
  carry their requested tag, including preview tags, independently of the source default.
- Packaging verifies every bundled asset against the source after extracting the
  ZIP. The packaged GUI check now requires the remastered window icon and all 72
  cached plane headings, and checks the running build version.
- The portable ZIP includes these notes. The release workflow uses them when
  preparing a Beta 6 draft; other tags retain generated notes.
- README changes since Beta 5 clarify handmade artwork and AI-assisted development.

## Comparison with the published Beta 5

Verified on October 29, 2026: published `v0.9.0-beta-5` points to `a3fe82b`;
local and GitHub `main` both point to `11b12d4`. Before this preparation, the
tree difference was only README.md (11 insertions, one deletion).

Beta 5 already shipped traffic strips, `Plane_remastered.png`, five-degree
radar rotation, and the portable Windows build with extracted-ZIP smoke testing.
Those features are retained here, not newly introduced in Beta 6. Beta 5 was
published October 14, 2026 with a Windows x64 ZIP and SHA-256 file.

## Running the portable edition

Extract the entire ZIP and launch `LtATC/LtATC.exe`, keeping `_internal` beside
it. Python is not required. Progress uses `%LOCALAPPDATA%\LtATC\progress.json`.
The executable is unsigned. This educational prototype is not for operational ATC use.

## Release preparation

Build locally with Windows x64 Python 3.12 after installing requirements-build.txt:

```powershell
python scripts/build_portable.py v0.9.0-beta-6
```

No release date is assigned. Commit and review the prepared changes before any
future tag or workflow dispatch. Manual workflow dispatch with `create_draft`
unchecked produces artifacts only. Publishing requires a separate human action.
