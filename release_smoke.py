"""Exercise the real bundled GUI without touching the player's saved progress."""
import json
import traceback
from pathlib import Path
import tkinter as tk

from sandbox.persistence import load_scenario, save_scenario
from ui.main_window import ASSETS, MainWindow
from app_version import current_version


def run_smoke_test(report_path):
    root = None
    result = {"ok": False}
    try:
        root = tk.Tk()
        callback_errors = []
        root.report_callback_exception = lambda *args: callback_errors.append(str(args[1]))
        window = MainWindow(root)
        window._cancel_startup()
        # The build runner supplies an isolated LOCALAPPDATA directory.
        if len(window.images) != 18:
            raise RuntimeError("One or more required images did not load")
        frames = sorted((ASSETS / "startup_animation").glob("frame_*.png"))
        if not frames or not (ASSETS / "bedstead.otf").is_file():
            raise RuntimeError("Startup animation or bundled font is missing")
        for frame in frames:
            tk.PhotoImage(master=root, file=str(frame))
        window.show_menu()
        root.update()
        window.start_sandbox()
        if not window.window_icons or window.radar.plane_sprite is None:
            raise RuntimeError("Remastered window icon or plane sprite is missing")
        sprite = window.radar.plane_sprite
        for heading in range(0, 360, 5):
            sprite.at_heading(heading)
        if len(sprite.frames) != 72:
            raise RuntimeError("Heading sprite cache is incomplete")
        window.select_aircraft("ACADEMY 02")
        window.refresh()
        root.update()
        if not window.radar.find_withtag("exit_gate"):
            raise RuntimeError("Sandbox radar did not render")
        if "DEST EAST" not in window.aircraft_panel.label.cget("text"):
            raise RuntimeError("Flight strip did not render")
        scenario = Path(report_path).with_suffix(".scenario.json")
        save_scenario(scenario, window.sandbox)
        loaded = load_scenario(scenario)
        if loaded.simulation.get_aircraft("ACADEMY 02").destination != "EAST":
            raise RuntimeError("Scenario round trip failed")
        for mode in ("teletext", "dos", "radar"):
            window._set_display_mode(mode)
            window.refresh()
            root.update()
        if callback_errors:
            raise RuntimeError("GUI callbacks failed: " + "; ".join(callback_errors))
        result = {"ok": True, "version": current_version(), "images": len(window.images),
                  "animation_frames": len(frames), "sprite_frames": len(sprite.frames)}
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        if root is not None:
            root.destroy()
        Path(report_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1
