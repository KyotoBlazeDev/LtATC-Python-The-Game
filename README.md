# LtATC: Python The Game

<img width="900" height="360" alt="LtATC: Python The Game cover art" src="https://github.com/user-attachments/assets/7cbb980f-0eff-4f15-95bf-b3d5a14d5e06" />

**LtATC: Python The Game** is a Python/Tkinter educational air-traffic-control game with a fictional 1990s setting and a Windows 95-inspired visual identity. Read the radar, guide simulated aircraft, work through guided lessons, experiment in Sandbox, and explore source-labeled Story Mode decision studies based on documented aviation incidents.

The game combines its graphical radar with deliberately retro alternate displays, including a 40 × 25 Teletext view and an 80 × 25 DOS-style tactical console. Safety warnings, configurable Sandbox traffic, emergencies, scenario saving, keyboard navigation, and collision testing have grown from the original small prototype into the current public beta.

> **LtATC is a game.** Aircraft behavior, distances, warnings, clearances, and scenarios are simplified for gameplay. It is not intended for real-world air traffic control training or operational use.

<img width="1099" height="278" alt="LtATC: Python The Game logo" src="https://github.com/user-attachments/assets/d94e3394-95b7-4bab-95a0-95dcecce6ee5" />

## Current status

**Public beta — v0.9.0 Beta 3**

Release target: ~~**October 7, 2026**~~ **December 20, 2026**.

The project grew far beyond its original scope, so the release was rescheduled to allow more time for testing, polish, and school/exam responsibilities. Codex continues to assist and co-author development under human oversight; KyotoBlazeDev reviews, tests, and decides what becomes part of LtATC.

> [!IMPORTANT]
> ## AI usage disclaimer
> AI-assisted tools were used during development. The developer reviewed and integrated all resulting material. The developer remains responsible for the project's design, implementation, and published content.
> 
> The original concept, **Learn The ATC: Python Edition**, is a Tkinter educational game about four air traffic service functions, developed on September 11, 2026, under a private development build project; it may be public on the X posts (BlazeGamerzz, known as BlazeLegacy774) with a reference image.
>
> <img width="1920" height="1080" alt="Cuplikan layar 2026-09-11 212616" src="https://github.com/user-attachments/assets/1b816859-cb04-4b91-ac6e-3c2d83052faa" />
> 
> Story Mode is now a set of source-labeled decision studies based on documented NTSB incidents. The scenarios use schematic aircraft positions, simplified choices, and paraphrased summaries. They do not reproduce flight tracks, radio transcripts, or operational procedures.

## The game

LtATC presents a fictional 1990s air-traffic-control environment through a deliberately retro desktop interface. You interpret the radar picture, respond to simulated aircraft, and use the same underlying game systems through graphical, Teletext, and DOS-style views.

The Windows 95-inspired presentation is part of the game's identity, but the simulation underneath it has grown into multiple modes: guided Lessons, an open-ended Sandbox, and Story Mode decision studies. Everything remains simplified and game-oriented rather than an attempt to reproduce operational ATC software or procedures.

## Screenshots and visual identity

The cover art at the top represents LtATC's current public identity. The project began as **Learn The ATC: Python Edition** on September 11, 2026, and the original prototype screenshot preserved below shows how far the interface has evolved.


## Run

Use Python 3.11 or newer. No packages or network access are required.

```powershell
python main.py
```

## Gameplay / How to use
The Tkinter window opens at the main menu. Story Mode offers four case studies; Lesson Mode offers four separate guided exercises; Sandbox Mode is free experimentation without story consequences. Click an aircraft marker to select it. In Story Mode, use the **Story objective** decision buttons to review evidence, choose a safety response, and read the documented outcome. Standard clearance buttons are reserved for Lesson and Sandbox modes. Advance case narration with **Next dialogue**.

Lesson 4 guides ARRIVAL 04 through approach, a practice go-around, a second approach, a runway check, and landing. Follow the current objective in the lesson panel; completion requires the aircraft to stop and release the runway.

Sandbox **Traffic rate** now generates airborne traffic automatically: Low every 20 simulation seconds, Medium every 10, and High every 5. Manual disables automatic generation. Traffic enters at radar edges only when a position avoids predicted conflicts; a blocked attempt is skipped until the next interval. Generation respects pause, simulation speed, game over, and the 30-aircraft limit. Changing the rate restarts its interval. Weather and time settings remain labels.

The graphical radar shows a short aircraft trail and a yellow dashed **8-second target-direction preview** for the selected airborne aircraft. The preview uses target heading and speed, so it is a simplified projection rather than the actual curved turning path. Trails clear when traffic is removed or a scenario restarts.

Use the **Sandbox** menu for these activities:

- **Start three-minute shift** starts fresh traffic and increases the rate from Low to Medium to High each minute. Guide aircraft out of the sector or land them while maintaining separation. Manual spawning and removal are disabled during a shift. The report awards 100 points per aircraft handled plus one point per second without a current separation warning. Paused time does not count. Completion or collision freezes the shift; start another shift or use Simulation → Reset Scenario for regular Sandbox.
- **Trigger emergency** alternates a priority landing request and a 15-second runway inspection closure. The **Emergencies** checkbox attempts an event every 30 simulation seconds. Priority aircraft show red markers and a PRIORITY label in graphical radar, or `!` in character displays. Land the priority aircraft to resolve its request. A closure blocks landing clearances, shows CLOSED on radar, and reopens automatically; all event timers stop while paused. Events remain pending when traffic or runway conditions prevent them.
- **Save scenario / Load scenario** use portable JSON files containing aircraft, runway status, traffic and environment settings, speed, safety thresholds, and selected aircraft. Loading validates the whole file before replacing the scene and always pauses it. A bad file leaves the current scene intact. Saves are for regular Sandbox sessions; active or completed shifts and collision scenes cannot be saved. Progress and shift scores are separate from scenario files. Generation and emergency scheduling restart after loading; an active inspection closure retains its remaining duration.

Aircraft leaving the radar sector are removed automatically in Sandbox, so continuous traffic does not fill the aircraft limit with invisible targets.

Enter a controller name on the main menu (or lesson menu) to use it in Lesson and Sandbox dialogue, the status bar, and lesson reports. Leave it blank to use **Controller**. The name is kept only while the app is open and does not change Story Mode's source-labeled case files. Lesson and Story completion is saved locally between sessions; use **Reset progress** on the main menu to clear it.

The case studies unlock chronologically through four documented 1990s runway events: **Detroit in dense fog (1990)**, **Los Angeles runway collision (1991)**, **St. Louis wrong-runway entry (1994)**, and **Providence surface confusion (1999)**. Each chapter uses a schematic runway and simplified choices rather than recreating exact movement tracks or procedures. Chapter IDs remain stable so saved completion progress stays compatible. Each chapter shows its NTSB identifier and an **Open NTSB report** button. **Retry checkpoint** restores the latest decision stage. Sources: [Detroit 1990](https://www.ntsb.gov/investigations/Pages/DCA91MA010.aspx), [Los Angeles 1991](https://www.ntsb.gov/investigations/Pages/DCA91MA018.aspx), [St. Louis 1994](https://www.ntsb.gov/investigations/Pages/CHI95MA044.aspx), and [Providence 1999](https://www.ntsb.gov/safety/safety-recs/RecLetters/A00_66_71.pdf).

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
- `lessons/`: four reusable guided lessons
- `sandbox/`: free-play aircraft generation
- `story/`: characters, dialogue queue, four chapters, checkpoints, and in-memory progress
- `ui/`: Tkinter panels and radar presentation
- `assets/`: supplied artwork

`GameState` owns mode transitions, scene restarts, actor creation, and persisted completion progress. Repeated requests for the active lesson or chapter do nothing; Retry explicitly resets that scene. The core simulation is shared across all modes and independent of Tkinter. Aircraft positions in Story Mode are schematic and static; the decision studies are about reading documented risk and choosing a response, not recreating the exact event or training real-world procedures.

## Feedback
Bugs and pull requests are welcome; the Code of Conduct remains planned. These bugs are fixed and will be released soon. Suggestions are welcome if you have any questions about feature requests. Security and policy remain planned.
