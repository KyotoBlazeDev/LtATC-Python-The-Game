# LtATC: Python The Game

LtATC: Python The Game is an educational ATC game prototype inspired by Learn the ATC: Python Edition. It is not intended for real-world air traffic control training or operational use.

Developed by **KyotoBlazeDev**.

Release date: **October 7, 2026**.

## AI usage disclaimer

AI-assisted tools were used during development. All resulting material was reviewed and integrated under the developer's direction. The developer remains responsible for the project's design, implementation, and published content.

The source project, **Learn The ATC — Python Edition**, is a Tkinter educational game about four air traffic service functions. Story Mode is now a set of source-labeled decision studies based on documented NTSB incidents. The scenarios use schematic aircraft positions, simplified choices, and paraphrased summaries. They do not reproduce flight tracks, radio transcripts, or operational procedures.

The original story document identifies **TRAINER01 as the training program**, not an aircraft. Lesson aircraft therefore use the story's documented callsigns: **CARGO 90**, **ACADEMY 01**, **EAGLE 21**, and **JET 404**. Sandbox traffic begins with **ACADEMY 02** and continues the ACADEMY numbering. TRAINER01 remains available only as a program or dialogue identity.

## Run

Use Python 3.11 or newer. No packages or network access are required.

```bash
python main.py
```

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

## Code map

To try game over, open Sandbox, click **Collision demo**, then **Resume**. The demo replaces current traffic, switches training safety off, and sets two aircraft on a head-on course at 3,000 ft. Impact occurs after about four seconds at 1x speed. Turning training safety back on pauses them before collision. With safety off, heading and altitude commands may create predicted conflicts; numeric limits, aircraft-state checks, and runway availability checks still apply.

- `game/`: central `GameState` lifecycle, aircraft motion, clearances, runway, simulation, and safety rules
- `lessons/`: three reusable guided lessons
- `sandbox/`: free-play aircraft generation
- `story/`: characters, dialogue queue, four chapters, checkpoints, and in-memory progress
- `ui/`: Tkinter panels and radar presentation
- `assets/`: supplied artwork

`GameState` owns mode transitions, scene restarts, actor creation, and persisted completion progress. Repeated requests for the active lesson or chapter do nothing; Retry explicitly resets that scene. The core simulation is shared across all modes and independent of Tkinter. Aircraft positions in Story Mode are schematic and static; the decision studies are about reading documented risk and choosing a response, not recreating the exact event or training real-world procedures.
