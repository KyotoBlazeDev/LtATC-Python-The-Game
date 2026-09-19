# Contributing Guide for the LtATC
Welcome to contributing to the LtATC: Python The Game! Please read the contributing guidelines before you use
Any issues and bugs are appreciated. But it's important to read this.

## Contributing guide
*The Code of Conduct are planned*

# Contributing to LtATC

Thank you for your interest in contributing to **LtATC: Python The Game**.

LtATC is a Windows 95–inspired air traffic control training game built with Python and Tkinter. Contributions should preserve its educational purpose, retro presentation, and safety-focused design.

## Ways to Contribute

You can help by:

- Reporting bugs
- Improving documentation
- Fixing UI or DPI-scaling problems
- Improving accessibility
- Adding tests
- Improving lessons and Sandbox Mode
- Correcting historical information
- Suggesting carefully researched Incident Studies

## Reporting Bugs

Before submitting a report, check existing issues for duplicates.

Include:

- Operating system
- Python version
- Display resolution and scaling percentage
- Steps to reproduce the problem
- Expected and actual behavior
- Error messages or terminal output
- Screenshots when relevant

For Tk lifecycle problems, mention whether the issue occurred after:

- Switching between Radar, Teletext, and DOS
- Minimizing or restoring the game
- Opening or closing a dialog
- Deleting an active aircraft
- Returning to the main menu
- Changing display scaling

Do not include passwords, private files, or other sensitive information.

## Development Setup

Clone the repository:
```bash
git clone https://github.com/KyotoBlazeDev/LtATC-Python-The-Game.git
cd LtATC-Python-The-Game
```

Create a virtual environment:
```powershell
python -m venv .venv
```

Activate it on Windows:
```powershell
.venv\Scripts\Activate.ps1
```

Install the test dependency:
```bash
python -m pip install pytest
```

Run the game:
```bash
python main.py
```

## Running Tests

Run the complete test suite before submitting a pull request:
```bash
python -m pytest -q
```

Also check syntax:
```bash
python -m compileall -q game lessons sandbox story ui main.py
```

UI changes should be tested at:
- 100% scaling
- 125% scaling
- 150% scaling
- 175% scaling
Pay particular attention to long titles, wrapped text, status fields, menus, dialogs, and controls near the bottom of the window.

## Coding Guidelines
- Follow the existing project structure and coding style.
- Keep gameplay logic separate from Tkinter presentation where practical.
- Avoid introducing unnecessary dependencies.
- Preserve keyboard navigation and focus behavior.
- Do not create duplicate after() loops or event bindings.
- Ensure scheduled callbacks do not access destroyed widgets.
- Keep Radar, Teletext, and DOS display modes mutually exclusive.
- Add or update tests for behavioral changes.
- Do not commit .pyc, __pycache__, virtual environments, or local save files.

## Interface Guidelines
New UI should remain consistent with the Windows 95–inspired design:
- Use the shared theme in ui/theme.py.
- Prefer MS Sans Serif–style UI text.
- Reserve Fixedsys-style fonts for technical displays.
- Use classic square controls and restrained colors.
- Avoid rounded modern controls, gradients, and excessive animation.
- Maintain readability at every supported DPI scale.
Retro styling must not reduce usability or accessibility.

## Incident Study Guidelines
Incident Studies are based on real events and may involve fatalities.
Contributions must:
- Use authoritative sources such as official NTSB reports.
- Include a direct source link and investigation identifier.
- Clearly identify scenarios as simplified decision studies.
- Avoid inventing quotations, transcripts, or precise flight paths.
- Distinguish documented facts from simplified gameplay.
- Use factual, respectful, and non-sensational language.
- Focus on safety lessons rather than entertainment value.
Do not reproduce copyrighted reports or long passages verbatim.

## AI-Assisted Contributions
AI-assisted tools may be used, but contributors remain responsible for everything they submit.
You must:
- Review generated code and writing carefully.
- Verify historical and technical claims against authoritative sources.
- Test generated changes.
- Disclose substantial AI assistance in the pull request.
- Ensure the contribution does not contain fabricated sources or copied material.

## Pull Requests
Keep each pull request focused on one clear change.
A pull request should include:
- A concise description of the change
- The reason for the change
- Testing performed
- Screenshots for visible UI changes
- Sources for historical changes
- Any known limitations
