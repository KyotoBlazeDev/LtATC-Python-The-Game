# LtATC: Python The Game
A open-source game based on Tkinter using Tcl/Tk around Air Traffic Control.

*Learn the ATC: Python The Game* is a educational game using Tcl/tk-based classic. Nearly developed within 4 days from September 14, 2026, to September 18, 2026. Optional with `./venv` folder to create this. I would highly recommended using virtual environment based on Python documentation.

> [!NOTE]
> You must create `./venv` folder, this is dependent only on one machine.

## Plot
You control the air traffic control as controller; you must describe the radar and take action if aircraft is requesting different methods. They're all there, must be kind and communicate properly. All actions are simulated, not real ATC.

## Run

Use Python 3.11 or newer. No packages or network access are required.

```powershell
python main.py
```

## Gameplay / How to use
The Tkinter window opens at the main menu. Story Mode offers four case studies; Lesson Mode offers three separate guided exercises; Sandbox Mode is free experimentation without story consequences. Click an aircraft marker to select it. In Story Mode, use the **Story objective** decision buttons to review evidence, choose a safety response, and read the documented outcome. Standard clearance buttons are reserved for Lesson and Sandbox modes. Advance case narration with **Next dialogue**.

Enter a controller name on the main menu (or lesson menu) to use it in Lesson and Sandbox dialogue, the status bar, and lesson reports. Leave it blank to use **Controller**. The name is kept only while the app is open and does not change Story Mode's source-labeled case files. Lesson and Story completion is saved locally between sessions; use **Reset progress** on the main menu to clear it.

The case studies unlock in sequence: **JFK runway incursion (2023)**, **Austin in dense fog (2023)**, **Burbank converging traffic (2023)**, and **JFK crossing traffic (2024)**. Each case changes the schematic runway number and orientation: JFK uses 4L, Austin uses 18L, and Burbank uses 33. The fourth case uses a preliminary report. Each chapter shows its NTSB identifier and an **Open NTSB report** button. **Retry checkpoint** restores the latest decision stage. Sources: [JFK 2023](https://www.ntsb.gov/investigations/Pages/DCA23LA125.aspx), [Austin 2023](https://www.ntsb.gov/investigations/Pages/DCA23FA149.aspx), [Burbank 2023](https://data.ntsb.gov/carol-repgen/api/Aviation/ReportMain/GenerateNewestReport/106779/pdf), [JFK 2024 preliminary](https://data.ntsb.gov/carol-repgen/api/Aviation/ReportMain/GenerateNewestReport/194114/pdf).

Sandbox controls let you spawn or remove traffic, pause or resume, change simulation speed, and set simple weather, time, and traffic labels. Up to 30 unique aircraft can be active. Safety checks block invalid transmissions and predicted separation warnings appear on radar. Lesson 3 pauses at the training safety boundary and offers a safe retry.

Switching to another app or minimizing LtATC automatically pauses gameplay in every mode. When you return, click **Resume** to continue. Moving focus between controls within LtATC does not pause the game.

In Lesson and Sandbox, training safety pauses critical traffic before it can continue into a collision. With training safety off, an airborne collision ends the session: the radar freezes, the explosion artwork marks the impact, and **Retry** / **Main menu** remain available. Retry starts a fresh session with safety on. Collisions use fixed game distances (12 logical pixels horizontally and 100 feet vertically), independently of configurable separation alerts or whether warnings are visible. Swept movement checks catch aircraft crossing between frames. Teletext and DOS show a text game-over banner. Story Mode's static case studies retain their documented outcomes.

Sandbox also exposes configurable separation thresholds. **Warn px** controls the predicted horizontal warning distance, **Critical px** controls the current horizontal critical distance, and **Vertical ft** controls the vertical filter for both. Critical distance cannot exceed warning distance. **Defaults** restores 80 px warning, 40 px critical, and 1,000 ft vertical separation. These are simplified simulation values, not operational separation minima; starting another mode restores the defaults.

During gameplay, press **Tab** or **Shift+Tab** to cycle forward or backward through all aircraft, **1–9** to select the matching numbered aircraft on the radar, and **0** to clear the selection. Use **Ctrl+Tab** or **Ctrl+Shift+Tab** to move keyboard focus among the controls. Aircraft-selection shortcuts work in Story, Lesson, and Sandbox modes; mouse selection still works.

Choose **View → Teletext Display** during gameplay to open the 40 × 25 character display. It includes **P100 Radar**, **P101 Traffic**, **P102 Runway**, and **P103 Alerts**; P100 is the initial page. Aircraft remain clickable on P100, and keyboard selection shortcuts continue to work in character-display mode. The bundled Bedstead font loads automatically on Windows, with Consolas used as a fallback. Bedstead is by Ben Harris and dedicated to the public domain (CC0); see the [Bedstead source and license](https://github.com/textmodes/bedstead).

Choose **View → DOS Console** for a separate 80 × 25 blue-screen tactical view with a traffic roster and a `C:\LTATC>` command prompt. Type `HELP` to see commands. `DIR` lists the game's four virtual files, and `TYPE RADAR.SCR`, `TYPE TRAFFIC.DAT`, `TYPE RUNWAY.DAT`, or `TYPE ALERTS.LOG` reads live game information. `CLS`, `VER`, `STATUS`, `SELECT <callsign>`, `PAUSE`, and `RESUME` are also supported; Up recalls prior commands. These are in-game commands, not operating-system commands. DOS mode uses Modern DOS 8x16 when installed, with a Consolas fallback. DOS mode and Teletext display are mutually exclusive. Modern DOS 8x16 is by Jayvee Enaguas and is released under CC0; see the [font's provenance and license](https://github.com/susam/pcface#modern-dos-font). The DOS font is not bundled with the game.

## Image credits

Startup airport photograph by [Johannes Heel](https://unsplash.com/id/@j_heel?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on [Unsplash](https://unsplash.com/id/foto/sebuah-pesawat-besar-terbang-di-atas-landasan-pacu-XmLULwMRxcU?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText), used under the [Unsplash License](https://unsplash.com/id/lisensi). The project includes a resized PNG derivative for Tkinter alongside the downloaded source photograph.

## AI usage disclaimer

AI-assisted tools were used during development. All resulting material was reviewed and integrated under the developer's direction. The developer remains responsible for the project's design, implementation, and published content.
