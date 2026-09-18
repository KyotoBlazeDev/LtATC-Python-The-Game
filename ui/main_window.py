import logging
import time
import tkinter as tk
import tkinter.font as tkfont
import ctypes
import sys
from pathlib import Path
from tkinter import messagebox
from game.clearances import Clearance
from game.constants import AIRCRAFT_LIMIT, GameMode
from game.game_state import GameState
from lessons.lesson_manager import LESSONS
from story.dialogue import DialogueQueue
from story.persistence import default_progress_path
from story.story_manager import CHAPTERS
from game.events import GameEvent, EventType
from ui.aircraft_panel import AircraftPanel
from ui.control_panel import ControlPanel
from ui.dialogs import show_report, show_warning
from ui.lesson_panel import LessonPanel
from ui.radar_canvas import RadarCanvas
from ui.story_panel import StoryPanel
from ui.theme import CLASSIC_GRAY, classic_title_bar, apply_classic_theme

ASSETS = Path(__file__).resolve().parent.parent / "assets"

def load_bedstead(root):
    """Register the bundled font for this process on Windows."""
    font_path = ASSETS / "bedstead.otf"
    if not font_path.exists() or sys.platform != "win32":
        return
    try:
        ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0)
        root.tk.call("font", "families")
    except (OSError, AttributeError, tk.TclError):
        logging.warning("Bedstead font unavailable; using Consolas")

class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("LtATC: Python The Game")
        root.geometry("1100x700")
        root.minsize(760, 600)
        self.game = GameState(default_progress_path())
        self.simulation = self.game.simulation
        self.lessons = self.game.lessons
        self.story = self.game.story
        self.story_manager = self.game.story_manager
        self.dialogue = DialogueQueue()
        self.sandbox = self.game.sandbox
        self.player_name_var = tk.StringVar(value="")
        load_bedstead(root)
        apply_classic_theme(root)
        self.images = self._load_images()
        self.window_icons = ()
        try:
            plane_icon = tk.PhotoImage(file=str(ASSETS / "Plane.png"))
            self.window_icons = (plane_icon.subsample(6), plane_icon.subsample(10))
            root.iconphoto(True, *self.window_icons)
        except tk.TclError:
            logging.warning("Window icon unavailable: Plane.png")
        self.last_tick = time.monotonic()
        self.reported = False
        self.boundary_shown = False
        self.startup_job = None
        self.startup_frame_image = None
        self.frame = tk.Frame(root)
        self.frame.pack(fill="both", expand=True)
        self._build_menu_bar()
        self._build_status_bar()
        root.bind("<KeyPress>", self._select_aircraft_with_key, add="+")
        root.bind("<MouseWheel>", self._scroll_sidebar, add="+")
        self.show_startup()
        root.after(33, self.tick)

    def _build_menu_bar(self):
        """Create the application command surface using native classic menus."""
        menu_bar = tk.Menu(self.root, tearoff=False)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Main Menu", command=self.show_menu, accelerator="Ctrl+M")
        file_menu.add_separator()
        file_menu.add_command(label="Exit to System", command=self.root.destroy, accelerator="Alt+F4")
        menu_bar.add_cascade(label="File", menu=file_menu, underline=0)

        controller = tk.Menu(menu_bar, tearoff=False)
        controller.add_command(label="Select Next Aircraft", command=lambda: self._step_aircraft(1), accelerator="Tab")
        controller.add_command(label="Select Previous Aircraft", command=lambda: self._step_aircraft(-1), accelerator="Shift+Tab")
        controller.add_command(label="Clear Selection", command=lambda: self.select_aircraft(None), accelerator="0")
        controller.add_separator()
        controller.add_command(label="Spawn Aircraft", command=self.spawn_aircraft)
        controller.add_command(label="Remove Selected Aircraft", command=self.remove_selected, accelerator="Delete")
        controller.add_command(label="Clear All Aircraft", command=self.clear_all)
        controller.add_separator()
        controller.add_command(label="Aircraft Manager...", command=self._show_aircraft_manager)
        menu_bar.add_cascade(label="Controller", menu=controller, underline=0)

        simulation = tk.Menu(menu_bar, tearoff=False)
        simulation.add_command(label="Pause Simulation", command=self.simulation.pause, accelerator="P")
        simulation.add_command(label="Resume Simulation", command=self.simulation.resume, accelerator="R")
        self.menu_safety_var = tk.BooleanVar(value=True)
        simulation.add_checkbutton(label="Training Safety", variable=self.menu_safety_var,
                                   command=self._menu_toggle_safety)
        speed = tk.Menu(simulation, tearoff=False)
        for label, value in (("0.5x", .5), ("1.0x", 1), ("2.0x", 2)):
            speed.add_command(label=label, command=lambda v=value: self._set_speed(v))
        simulation.add_cascade(label="Simulation Speed", menu=speed)
        simulation.add_separator()
        simulation.add_command(label="Reset Scenario", command=self._reset_active_scenario)
        simulation.add_command(label="Collision Demonstration", command=self._start_collision_demo)
        menu_bar.add_cascade(label="Simulation", menu=simulation, underline=0)
        self.simulation_menu = simulation

        view = tk.Menu(menu_bar, tearoff=False)
        view.add_command(label="Radar Display", command=self._show_radar_display)
        view.add_command(label="Teletext Display", command=lambda: self._set_display_mode("teletext"))
        view.add_command(label="DOS Console", command=lambda: self._set_display_mode("dos"))
        menu_bar.add_cascade(label="View", menu=view, underline=0)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="Keyboard Controls", command=self._show_keyboard_help)
        help_menu.add_separator()
        help_menu.add_command(label="About LtATC...", command=self._show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu, underline=0)
        self.root.configure(menu=menu_bar)
        self.menu_bar = menu_bar
        self.root.bind("<Control-m>", lambda _event: self.show_menu(), add="+")
        self.root.bind("<KeyPress-p>", self._pause_shortcut, add="+")
        self.root.bind("<KeyPress-r>", self._resume_shortcut, add="+")

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bd=1, relief="raised", bg="#c0c0c0")
        # Pack before the expanding content frame so the game cannot consume
        # the status bar's allocation at smaller window sizes.
        bar.pack(fill="x", side="bottom", before=self.frame)
        self.status_fields = []
        for width in (18, 7, 12, 17, 24):
            field = tk.Label(bar, width=width, padx=4, pady=3, relief="sunken", bd=1,
                             anchor="w", font="LtATCFixedFont", bg=CLASSIC_GRAY)
            field.pack(side="left", fill="x", expand=width == 24, padx=(1, 0), pady=1)
            self.status_fields.append(field)
        # Compatibility handle for existing integrations which configure the status text.
        self.status = self.status_fields[0]

    def _set_status(self, *fields):
        for widget, value in zip(self.status_fields, fields):
            widget.configure(text=value)

    def _step_aircraft(self, direction):
        callsigns = tuple(self.simulation.aircraft)
        if not callsigns:
            return
        current = self.simulation.selected_callsign
        index = callsigns.index(current) if current in callsigns else (-1 if direction > 0 else 0)
        self.select_aircraft(callsigns[(index + direction) % len(callsigns)])

    def _set_speed(self, value):
        self.simulation.set_speed(value)
        self.refresh()

    def _menu_toggle_safety(self):
        self.simulation.training_safety = self.menu_safety_var.get()
        self.refresh()

    def _pause_shortcut(self, event=None):
        if event is not None and isinstance(event.widget, (tk.Entry, tk.Text, tk.Spinbox)):
            return
        if self.simulation.mode != GameMode.MAIN_MENU:
            self.simulation.pause()
            self.refresh()

    def _resume_shortcut(self, event=None):
        if event is not None and isinstance(event.widget, (tk.Entry, tk.Text, tk.Spinbox)):
            return
        if self.simulation.mode != GameMode.MAIN_MENU:
            self.simulation.resume()
            self.refresh()

    def _reset_active_scenario(self):
        if self.simulation.mode == GameMode.STORY:
            self.retry_story_checkpoint()
        elif self.simulation.mode in {GameMode.LESSON, GameMode.SANDBOX}:
            self.retry_game()

    def _start_collision_demo(self):
        if self.simulation.mode == GameMode.SANDBOX:
            self.start_sandbox(collision_demo=True)
        else:
            messagebox.showinfo("LtATC Collision Demonstration",
                                "The collision demonstration is available during Sandbox Control.",
                                parent=self.root)

    def _show_aircraft_manager(self):
        if self.simulation.mode != GameMode.SANDBOX:
            messagebox.showinfo("LtATC Aircraft Manager", "Aircraft Manager is available during Sandbox Control.", parent=self.root)
            return
        callsigns = "\n".join(self.simulation.aircraft) or "No aircraft are active."
        messagebox.showinfo("LtATC Aircraft Manager", f"ACTIVE AIRCRAFT\n\n{callsigns}\n\nSelect a target on radar; press Delete to remove it.", parent=self.root)

    def _set_display_mode(self, mode):
        if not hasattr(self, "teletext_enabled"):
            return
        self.teletext_enabled.set(mode == "teletext")
        self.dos_enabled.set(mode == "dos")
        if mode == "dos":
            self._toggle_dos()
        else:
            self.dos_console.pack_forget()
            self.radar.set_dos(False)
            self._toggle_teletext()

    def _show_radar_display(self):
        self._set_display_mode("radar")

    def _show_keyboard_help(self):
        messagebox.showinfo("LtATC Keyboard Controls", "Alt+F/C/S/V/H  Open application menus\nAlt+S/L/B  Start Story, Lesson, or Sandbox\nTab / Shift+Tab  Select aircraft\n1–9  Select aircraft directly\n0  Clear selection\nDelete  Remove selected sandbox aircraft\nP / R  Pause or resume", parent=self.root)

    def _show_about(self):
        messagebox.showinfo(
            "About LtATC",
            "LtATC: Python The Game\n"
            "Air Traffic Control Training Simulator\n\n"
            "Developed by KyotoBlazeDev\n\n"
            "Release date: October 7, 2026\n\n"
            "AI USAGE DISCLAIMER\n"
            "AI-assisted tools were used during development. All resulting material was "
            "reviewed and integrated under the developer's direction.\n\n"
            "This game is educational entertainment and is not approved for real-world "
            "air traffic control training or operational use.\n\n"
            "CONFIDENCE != CORRECTNESS",
            parent=self.root,
        )

    def _select_aircraft_with_key(self, event):
        if self.simulation.mode == GameMode.MAIN_MENU:
            return
        key = event.keysym
        if key in {"Tab", "ISO_Left_Tab"} and event.state & 0x0004:
            backwards = key == "ISO_Left_Tab" or bool(event.state & 0x0001)
            target = event.widget.tk_focusPrev() if backwards else event.widget.tk_focusNext()
            if target is not None:
                target.focus_set()
            return "break"
        if event.state & 0x000C:
            return
        if isinstance(event.widget, (tk.Entry, tk.Text, tk.Spinbox)):
            return
        if key == "Delete" and self.simulation.mode == GameMode.SANDBOX:
            self.remove_selected()
            return "break"
        callsigns = tuple(self.simulation.aircraft)
        if not callsigns:
            return
        if key in {"Tab", "ISO_Left_Tab"}:
            current = self.simulation.selected_callsign
            backwards = key == "ISO_Left_Tab" or bool(event.state & 0x0001)
            index = callsigns.index(current) if current in callsigns else (0 if backwards else -1)
            step = -1 if backwards else 1
            self.select_aircraft(callsigns[(index + step) % len(callsigns)])
        elif key in {str(i) for i in range(1, 10)} and int(key) <= len(callsigns):
            self.select_aircraft(callsigns[int(key) - 1])
        elif key == "0":
            self.select_aircraft(None)
        else:
            return
        return "break"

    def _scroll_sidebar(self, event):
        if self.simulation.mode == GameMode.MAIN_MENU or not hasattr(self, "sidebar_canvas"):
            return
        sidebar = self.sidebar_canvas
        x = event.x_root - sidebar.winfo_rootx()
        y = event.y_root - sidebar.winfo_rooty()
        if 0 <= x < sidebar.winfo_width() and 0 <= y < sidebar.winfo_height() and event.delta:
            sidebar.yview_scroll(-3 if event.delta > 0 else 3, "units")
            return "break"

    def _load_images(self):
        images = {}
        for key, filename, factor in (("logo", "LtATC_Python_The_Game_logo.png", 2),
                                       ("startup", "startup_radar_1990s.png", 2),
                                       ("startup_airport", "startup_airport_photo.png", 2),
                                       ("Blaze", "BlazeFerrende_avatar_bust.png", 11),
                                       ("Mervyn", "Mervyn.png", 7),
                                       ("plane_marker", "Plane.png", 10),
                                       ("emblem", "Wingsley_Emblem.png", 11),
                                       ("selected_frame", "selected_frame.png", 12),
                                       ("unselected_frame", "unselected_frame.png", 12),
                                       ("paused", "paused.png", 2),
                                       ("critical", "critical.png", 2),
                                       ("explosion", "boom_explosion.png", 6),
                                        ("separation_warning_frame", "separation_warnings_frame.png", 12),
                                        ("separation_critical_frame", "separation_critical_frame.png", 12),
                                        ("directional_prompt", "arrow cyan_facing.png", 12),
                                        ("training_note", "Training_note_message.png", 2),
                                        ("separation_warning", "separation_warnings.png", 2),
                                        ("green_mark", "green_mark.png", 12)):
            try:
                images[key] = tk.PhotoImage(file=str(ASSETS / filename)).subsample(factor)
            except tk.TclError:
                logging.warning("Asset unavailable: %s", filename)
        return images

    def _clear(self):
        for child in self.frame.winfo_children():
            child.destroy()

    @property
    def player_name(self):
        return self.player_name_var.get().strip()[:24] or "Controller"

    def _player_name_input(self, parent):
        tk.Label(parent, text="Controller name:", anchor="w").pack(fill="x", pady=(8, 2))
        tk.Entry(parent, textvariable=self.player_name_var, width=28).pack(pady=(0, 8))

    def _cancel_startup(self):
        if self.startup_job is not None:
            try:
                self.root.after_cancel(self.startup_job)
            except tk.TclError:
                pass
            self.startup_job = None
        self.startup_frame_image = None

    def show_startup(self):
        """Run a compact VGA-era boot sequence before the main menu."""
        self.game.enter_menu()
        self._cancel_startup()
        frames = sorted((ASSETS / "startup_animation").glob("frame_*.png"))
        if not frames:
            self._show_startup_stage(0)
            return
        timings_path = ASSETS / "startup_animation" / "timings_ms.txt"
        try:
            durations = [max(20, int(value)) for value in timings_path.read_text().splitlines() if value.strip()]
        except (OSError, ValueError):
            durations = []
        self._clear()
        shell = tk.Frame(self.frame, bg="#000000", bd=2, relief="sunken")
        shell.pack(expand=True, padx=16, pady=12)
        screen = tk.Canvas(shell, width=800, height=450, bg="#000000",
                           highlightthickness=1, highlightbackground="#777777")
        screen.pack()
        image_item = screen.create_image(400, 218)
        screen.create_text(400, 425, text="CLICK TO SKIP", fill="#909090",
                           font=("Fixedsys", 10))
        screen.bind("<Button-1>", lambda _event: self.show_menu())
        self._set_status("STARTUP", "5 FPS", "SAFETY ON", "AIRCRAFT 00/30", "CLICK TO SKIP")
        self._play_startup_frame(screen, image_item, frames, durations, 0)

    def _play_startup_frame(self, screen, image_item, frames, durations, index):
        if index >= len(frames) or not screen.winfo_exists():
            self.show_menu()
            return
        try:
            self.startup_frame_image = tk.PhotoImage(file=str(frames[index]))
            screen.itemconfigure(image_item, image=self.startup_frame_image)
        except tk.TclError:
            logging.warning("Startup animation frame unavailable: %s", frames[index])
            self._show_startup_stage(0)
            return
        duration = durations[index] if index < len(durations) else 200
        self.startup_job = self.root.after(
            duration, self._play_startup_frame, screen, image_item, frames, durations, index + 1)

    def _show_startup_stage(self, stage):
        self._cancel_startup()
        self._clear()
        shell = tk.Frame(self.frame, bg="#000000", bd=2, relief="sunken")
        shell.pack(expand=True, padx=16, pady=12)
        screen = tk.Canvas(shell, width=800, height=560, bg="#000000",
                           highlightthickness=1, highlightbackground="#999999")
        screen.pack()
        mono = ("Fixedsys", 13)

        if stage == 0:
            boot = (
                "Starting LtATC...\n\n"
                "640 KB Base Memory ........................ OK\n"
                "4,096 KB Extended Memory ................. OK\n"
                "VGA Display Detected (640x480, 256 colors)\n"
                "Mouse Initialized\n"
                "Sound Blaster Compatible Device... Not Found\n"
                "Loading TK Classic Interface.............. OK\n"
                "Loading LtATC Core Modules................ OK\n\n"
                "Please wait..._"
            )
            screen.create_text(18, 18, text=boot, fill="#e8e8e8", anchor="nw",
                               justify="left", font=mono)
            delay = 3000
            status = "SYSTEM BOOT | CHECKING BASE MEMORY AND DISPLAY"
        elif stage == 1:
            startup = self.images.get("startup")
            if startup:
                screen.create_image(400, 280, image=startup)
                screen.create_rectangle(105, 365, 695, 500, fill="#020806", outline="#2f7fff", width=2)
            logo = self.images.get("logo")
            if logo:
                screen.create_image(400, 245, image=logo)
            else:
                screen.create_text(400, 235, text="LtATC", fill="#3f80ff",
                                   font=("Fixedsys", 52, "bold"))
            screen.create_text(400, 397, text="PYTHON THE GAME", fill="#e8e8e8",
                               font=("Fixedsys", 22, "bold"))
            screen.create_text(400, 438, text="AIR TRAFFIC CONTROL TRAINING SIMULATOR",
                               fill="#dce9ff", font=("Fixedsys", 13))
            screen.create_text(400, 474, text="LEARN.  PRACTICE.  CONTROL.",
                               fill="#4b8eff", font=("Fixedsys", 15, "italic"))
            delay = 2800
            status = "LTATC DISPLAY | VERSION 1.0 | INITIALIZING"
        elif stage == 2:
            screen.configure(bg="#c0c0c0")
            screen.create_rectangle(15, 15, 785, 545, fill="#c0c0c0", outline="#ffffff", width=2)
            screen.create_rectangle(24, 25, 776, 61, fill="#000080", outline="")
            screen.create_text(42, 43, text="LtATC: Initializing", fill="#ffffff",
                               anchor="w", font=("Fixedsys", 15))
            modules = ("airport data", "aircraft database", "procedures", "radar module",
                       "training scenarios", "graphics")
            for index, module in enumerate(modules):
                y = 100 + index * 38
                screen.create_text(55, y, text=f"Loading {module:<22} ............",
                                   fill="#101010", anchor="w", font=mono)
                screen.create_text(710, y, text="OK", fill="#087829", anchor="e",
                                   font=("Fixedsys", 13, "bold"))
            screen.create_text(55, 350, text="Finalizing setup ...", fill="#101010",
                               anchor="w", font=mono)
            screen.create_rectangle(55, 393, 690, 433, fill="#ffffff", outline="#303030")
            for x in range(62, 616, 22):
                screen.create_rectangle(x, 399, x + 16, 427, fill="#0000a8", outline="#4e70ff")
            screen.create_text(720, 413, text="86%", fill="#101010", font=mono)
            screen.create_text(55, 480, text="Please wait...", fill="#101010", anchor="w", font=mono)
            delay = 3500
            status = "LOADING MODULES | RADAR AND TRAINING DATABASES"
        else:
            airport = self.images.get("startup_airport")
            screen.create_rectangle(40, 35, 760, 525, fill="#c0c0c0", outline="#ffffff", width=2)
            screen.create_rectangle(48, 43, 752, 78, fill="#000080", outline="")
            screen.create_text(400, 60, text="Training Tip", fill="#ffffff",
                               font=("Fixedsys", 15))
            if airport:
                screen.create_image(235, 276, image=airport)
            screen.create_text(565, 230,
                               text='"Good communication\nprevents confusion,\nand confusion\nprevents accidents."\n\n— ACADEMY',
                               fill="#101010", justify="center", font=("Fixedsys", 15))
            screen.create_text(235, 414, text="Photo: Johannes Heel / Unsplash",
                               fill="#303030", font=("Fixedsys", 9))
            screen.create_text(400, 493, text="System ready.", fill="#101010",
                               font=("Fixedsys", 13, "bold"))
            tk.Button(shell, text="PRESS TO CONTINUE", command=self.show_menu,
                      font=("Fixedsys", 12, "bold"), padx=28).pack(pady=7)
            delay = None
            status = "SYSTEM READY | PRESS TO CONTINUE"

        if stage < 3:
            screen.bind("<Button-1>", lambda _event, next_stage=stage + 1:
                        self._show_startup_stage(next_stage))
        else:
            screen.bind("<Button-1>", lambda _event: self.show_menu())
        self._set_status(status, "", "", "", "")
        if delay is not None:
            self.startup_job = self.root.after(delay, self._show_startup_stage, stage + 1)

    def show_menu(self):
        self._cancel_startup()
        self.game.enter_menu()
        self._clear()
        panel = tk.Frame(self.frame, bg="#000000", padx=36, pady=24)
        panel.pack(fill="both", expand=True)
        if self.images.get("logo"):
            tk.Label(panel, image=self.images["logo"], bg="#000000").pack(pady=(18, 4))
        else:
            tk.Label(panel, text="LtATC", fg="#4f8dff", bg="#000000",
                     font=("Fixedsys", 48, "bold")).pack(pady=(20, 4))
        tk.Label(panel, text="PYTHON THE GAME", fg="#d8d8d8", bg="#000000",
                 font=("Fixedsys", 18, "bold")).pack()
        tk.Label(panel, text="AIR TRAFFIC CONTROL TRAINING SIMULATOR", fg="#dce9ff",
                 bg="#000000", font=("Fixedsys", 11)).pack(pady=(2, 14))

        menu = tk.Frame(panel, bg="#c0c0c0", bd=3, relief="raised", padx=12, pady=10)
        menu.pack()
        classic_title_bar(menu, "LtATC Control Center").pack(fill="x", pady=(0, 8))
        tk.Label(menu, text="Controller name:", bg=CLASSIC_GRAY, anchor="w").pack(fill="x")
        tk.Entry(menu, textvariable=self.player_name_var, width=30,
                 font="TkDefaultFont").pack(pady=(2, 8))
        menu_buttons = []
        for label, mnemonic, command in (("> START STORY MODE", 2, self.show_story_menu),
                                         ("  LESSON TRAINING", 2, self.show_lesson_menu),
                                         ("  SANDBOX CONTROL", 2, self.start_sandbox),
                                         ("  RESET PROGRESS", 2, self.reset_progress),
                                         ("  EXIT TO SYSTEM", 2, self.root.destroy)):
            button = tk.Button(menu, text=label, command=command, anchor="w", width=28,
                               underline=mnemonic, takefocus=True)
            button.pack(fill="x", pady=2)
            menu_buttons.append(button)
        # Tk draws the classic dotted focus rectangle when these buttons own focus.
        menu_buttons[0].focus_set()
        self.root.bind("<Alt-s>", lambda _event: self.show_story_menu(), add="+")
        self.root.bind("<Alt-l>", lambda _event: self.show_lesson_menu(), add="+")
        self.root.bind("<Alt-b>", lambda _event: self.start_sandbox(), add="+")
        tk.Label(panel, text="REAL TRAFFIC.  REAL DECISIONS.  A BRIGHTER TOMORROW.",
                 fg="#75b8ff", bg="#000000", font=("Fixedsys", 11)).pack(pady=(16, 4))
        tk.Label(panel, text="CONFIDENCE != CORRECTNESS", fg="#b8c8c0", bg="#000000",
                 font=("Fixedsys", 10)).pack()
        self.refresh()

    def reset_progress(self):
        if not messagebox.askyesno("Reset progress", "Clear all lesson and story progress? This cannot be undone."):
            return
        if not self.game.reset_progress():
            messagebox.showerror("Reset failed", "Progress could not be reset. Check that the progress folder is writable.")
            return
        self.story = self.game.story
        self.story_manager = self.game.story_manager
        self.show_menu()

    def show_lesson_menu(self):
        self.game.enter_menu()
        self._clear()
        desktop = tk.Frame(self.frame, bg="#008080", padx=30, pady=30)
        desktop.pack(fill="both", expand=True)
        panel = tk.Frame(desktop, bd=3, relief="raised", padx=10, pady=8)
        panel.pack(expand=True)
        classic_title_bar(panel, "LtATC Training Manager").pack(fill="x", pady=(0, 8))
        tk.Label(panel, text="Select a training lesson", font="LtATCTitleFont", anchor="w").pack(fill="x", pady=(2, 6))
        self._player_name_input(panel)
        for lesson in LESSONS:
            completed = lesson.lesson_id in self.story.lessons_completed
            tk.Button(panel, text=lesson.title, anchor="w",
                       image=self.images.get("green_mark") if completed else "", compound="right",
                       command=lambda lid=lesson.lesson_id: self.start_lesson(lid)).pack(fill="x", pady=6)
        tk.Button(panel, text="Back", command=self.show_menu).pack(fill="x", pady=12)
        self.refresh()

    def show_story_menu(self):
        self.game.enter_menu()
        self._clear()
        desktop = tk.Frame(self.frame, bg="#008080", padx=30, pady=30)
        desktop.pack(fill="both", expand=True)
        panel = tk.Frame(desktop, bd=3, relief="raised", padx=10, pady=8)
        panel.pack(expand=True)
        classic_title_bar(panel, "LtATC Incident Studies").pack(fill="x", pady=(0, 8))
        tk.Label(panel, text="Story Mode", font="LtATCTitleFont").pack(pady=(2, 6))
        tk.Label(panel, text="Four simplified decision studies based on documented NTSB incidents.\n"
                              "Aircraft positions are schematic; each case links to its report.",
                  justify="center", wraplength=500).pack(pady=(0, 12))
        for chapter in CHAPTERS:
            unlocked = self.story_manager.unlocked(chapter.chapter_id)
            completed = chapter.chapter_id in self.story.chapters_completed
            suffix = " 🔒" if not unlocked else ""
            tk.Button(panel, text=chapter.title + suffix, anchor="w",
                       image=self.images.get("green_mark") if completed else "", compound="right",
                       state="normal" if unlocked else "disabled",
                       command=lambda cid=chapter.chapter_id: self.start_chapter(cid)).pack(fill="x", pady=6)
        tk.Button(panel, text="Back", command=self.show_menu).pack(fill="x", pady=12)
        self.refresh()

    def start_chapter(self, chapter_id, *, restart=False):
        self._cancel_startup()
        if not self.game.start_chapter(chapter_id, restart=restart):
            return
        chapter = self.story_manager.current
        self.dialogue.clear()
        for speaker, message in chapter.introduction:
            self.dialogue.show(speaker, message)
        self.reported = self.boundary_shown = False
        self._build_game()
        logging.info("Story chapter %s started.", chapter_id)

    def start_lesson(self, lesson_id, *, restart=False):
        self._cancel_startup()
        if not self.game.start_lesson(lesson_id, restart=restart):
            return
        lesson = self.lessons.current
        self.dialogue.clear()
        for speaker, message in lesson.introduction:
            self.dialogue.show(speaker, message.replace("{player}", self.player_name))
        self.reported = self.boundary_shown = False
        self._build_game()
        logging.info("Lesson %s started.", lesson_id)

    def start_sandbox(self, *, restart=False, collision_demo=False):
        self._cancel_startup()
        if not self.game.start_sandbox(restart=restart, collision_demo=collision_demo):
            return
        self.sandbox = self.game.sandbox
        self.dialogue.clear()
        if collision_demo:
            self.dialogue.show("System", "Collision demo ready. Click Resume: these two aircraft will collide in about 4 seconds. Training safety is off.")
        else:
            self.dialogue.show("Blaze", f"{self.player_name}, Sandbox is open. Experiment, inspect the traffic, and verify your clearances.")
        self._build_game()
        logging.info("Sandbox enabled.")

    def retry_game(self):
        if self.simulation.mode == GameMode.LESSON:
            self.start_lesson(self.game.active_id, restart=True)
        elif self.simulation.mode == GameMode.SANDBOX:
            self.start_sandbox(restart=True)

    def _build_game(self):
        self._clear()
        toolbar = tk.Frame(self.frame, padx=4, pady=4)
        toolbar.pack(fill="x")
        navigation = tk.Frame(toolbar)
        navigation.pack(fill="x")
        tk.Button(navigation, text="Main menu", command=self.show_menu).pack(side="left")
        if self.simulation.mode == GameMode.LESSON:
            tk.Button(navigation, text="Lessons", command=self.show_lesson_menu).pack(side="left", padx=4)
            tk.Button(navigation, text="Retry", command=lambda: self.start_lesson(self.lessons.current.lesson_id, restart=True)).pack(side="left")
        elif self.simulation.mode == GameMode.STORY:
            tk.Button(navigation, text="Story chapters", command=self.show_story_menu).pack(side="left", padx=4)
            tk.Button(navigation, text="Retry checkpoint", command=self.retry_story_checkpoint).pack(side="left")
        else:
            tk.Button(navigation, text="Collision demo", command=self._start_collision_demo).pack(side="left", padx=4)
            self._build_sandbox_toolbar(toolbar)
        self.teletext_enabled = tk.BooleanVar(value=False)
        self.dos_enabled = tk.BooleanVar(value=False)
        families = tkfont.families(self.root)
        character_fonts = [name for name in ("Bedstead", "Modern DOS 8x16") if name in families]
        if not character_fonts:
            character_fonts = ["Consolas"]
        self.character_font = tk.StringVar(value=character_fonts[0])
        self.teletext_pages = ("P100 Radar", "P101 Traffic", "P102 Runway", "P103 Alerts")
        self.teletext_page = tk.StringVar(value=self.teletext_pages[0])
        self.dos_console = tk.Frame(toolbar)
        self.dos_output = tk.Label(self.dos_console, text="Type HELP for commands.",
                                   bg="#0000aa", fg="#ffffff", anchor="w", justify="left",
                                   wraplength=750,
                                   font=("Modern DOS 8x16" if "Modern DOS 8x16" in families else "Consolas", 10))
        self.dos_output.pack(fill="x")
        prompt = tk.Frame(self.dos_console)
        prompt.pack(fill="x")
        tk.Label(prompt, text="C:\\LTATC>").pack(side="left")
        self.dos_entry = tk.Entry(prompt)
        self.dos_entry.pack(side="left", fill="x", expand=True)
        self.dos_entry.bind("<Return>", self._run_dos_command)
        self.dos_entry.bind("<Up>", self._dos_history_up)
        self.dos_history = []
        self.dos_history_index = 0
        body = tk.Frame(self.frame)
        self.game_body = body
        self.game_over_panel = tk.Frame(self.frame, padx=8, pady=8)
        self.game_over_reason = tk.Label(self.game_over_panel, wraplength=650)
        self.game_over_reason.pack(fill="x")
        tk.Button(self.game_over_panel, text="Retry", command=self.retry_game).pack(side="left", pady=4)
        tk.Button(self.game_over_panel, text="Main menu", command=self.show_menu).pack(side="left", padx=6)
        body.pack(fill="both", expand=True)
        self.radar = RadarCanvas(body, self.select_aircraft, self.images.get("plane_marker"),
                                 self.images.get("selected_frame"), self.images.get("unselected_frame"),
                                 self.images.get("paused"), self.images.get("critical"),
                                 self.images.get("separation_warning_frame"),
                                 self.images.get("separation_critical_frame"),
                                 self.images.get("directional_prompt"),
                                 self.images.get("separation_warning"), self.images.get("explosion"))
        sidebar = tk.Frame(body, width=360)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)
        scrollbar = tk.Scrollbar(sidebar, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.sidebar_canvas = tk.Canvas(sidebar, highlightthickness=0,
                                        background=self.root.cget("background"))
        self.sidebar_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.sidebar_canvas.yview)
        self.sidebar_canvas.configure(yscrollcommand=scrollbar.set)
        right = tk.Frame(self.sidebar_canvas, padx=5, pady=5)
        sidebar_window = self.sidebar_canvas.create_window((0, 0), window=right, anchor="nw")
        right.bind("<Configure>", lambda event: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all")))
        self.sidebar_canvas.bind("<Configure>", lambda event: self.sidebar_canvas.itemconfigure(sidebar_window, width=event.width))
        self.radar.pack(side="left", fill="both", expand=True)
        self.lesson_panel = LessonPanel(right, self.next_dialogue, self.check_runway)
        self.lesson_panel.pack(fill="x", pady=4)
        self.story_panel = None
        if self.simulation.mode == GameMode.STORY:
            self.story_panel = StoryPanel(right, self.story_action)
            self.story_panel.pack(fill="x", pady=4)
        self.aircraft_panel = AircraftPanel(right)
        self.aircraft_panel.pack(fill="x", pady=4)
        self.controls = ControlPanel(right, self.issue_clearance)
        self.controls.pack(fill="x", pady=4)
        self.refresh()

    def _toggle_teletext(self):
        if self.teletext_enabled.get():
            self.dos_enabled.set(False)
            self.dos_console.pack_forget()
        self.radar.set_teletext(self.teletext_enabled.get(), self.character_font.get())
        self.radar.set_teletext_page(int(self.teletext_page.get()[1:4]))
        self.refresh()

    def _choose_teletext_page(self):
        self.teletext_enabled.set(True)
        self._toggle_teletext()

    def _step_teletext_page(self, direction):
        index = self.teletext_pages.index(self.teletext_page.get())
        self.teletext_page.set(self.teletext_pages[(index + direction) % len(self.teletext_pages)])
        self._choose_teletext_page()

    def _toggle_dos(self):
        if self.dos_enabled.get():
            self.teletext_enabled.set(False)
            self.dos_console.pack(fill="x", pady=(3, 0))
            self.dos_entry.focus_set()
        else:
            self.dos_console.pack_forget()
        self.radar.set_dos(self.dos_enabled.get())
        self.refresh()

    def _dos_history_up(self, event):
        if self.dos_history:
            self.dos_history_index = max(0, self.dos_history_index - 1)
            self.dos_entry.delete(0, "end")
            self.dos_entry.insert(0, self.dos_history[self.dos_history_index])
        return "break"

    def _run_dos_command(self, event=None):
        raw = self.dos_entry.get().strip()
        self.dos_entry.delete(0, "end")
        if not raw:
            return "break"
        self.dos_history.append(raw)
        self.dos_history_index = len(self.dos_history)
        words = raw.upper().split()
        command = words[0]
        args = words[1:]
        simulation = self.simulation
        if command == "HELP":
            output = "HELP DIR TYPE <FILE> CLS VER STATUS SELECT <CALLSIGN> PAUSE RESUME"
        elif command == "DIR":
            output = "RADAR.SCR  TRAFFIC.DAT  RUNWAY.DAT  ALERTS.LOG\n4 virtual files in C:\\LTATC"
        elif command == "CLS":
            output = ""
        elif command == "VER":
            output = "LtATC DOS display 1.0"
        elif command == "STATUS":
            output = (f"{simulation.mode.name} | {len(simulation.aircraft)} aircraft | "
                      f"RWY {simulation.runway.name} | {'PAUSED' if simulation.paused else 'ACTIVE'}")
        elif command == "TYPE" and len(args) == 1:
            filename = args[0]
            if filename == "RADAR.SCR":
                output = "Radar view active. Use mouse or 1-9 to select a target."
            elif filename == "TRAFFIC.DAT":
                output = ", ".join(simulation.aircraft) or "NO AIRCRAFT"
            elif filename == "RUNWAY.DAT":
                output = f"RWY {simulation.runway.name}: {simulation.runway.occupied_by or 'CLEAR'}"
            elif filename == "ALERTS.LOG":
                conflicts = simulation.safety.conflicts(list(simulation.aircraft.values()))
                output = "; ".join(f"{item.first}/{item.second}" for item in conflicts) or "NO CURRENT ALERTS"
            else:
                output = "File not found"
        elif command == "SELECT" and args:
            requested = " ".join(args)
            callsign = next((name for name in simulation.aircraft if name.upper() == requested), None)
            if callsign:
                self.select_aircraft(callsign)
                output = f"SELECTED {callsign}"
            else:
                output = "Aircraft not found"
        elif command == "PAUSE":
            simulation.pause()
            output = "SIMULATION PAUSED"
        elif command == "RESUME":
            simulation.resume()
            output = "GAME OVER — use Retry or Main menu" if simulation.game_over else "SIMULATION RESUMED"
        else:
            output = "Bad command or file name. Type HELP."
        self.dos_output.configure(text=output or " ")
        self.refresh()
        return "break"

    def _build_sandbox_toolbar(self, bar):
        settings = tk.LabelFrame(bar, text="Environment", padx=3, pady=2)
        settings.pack(fill="x", pady=(3, 0))
        for label, variable, options in (("Traffic rate", "traffic_rate", ("Manual", "Low", "Medium", "High")),
                                         ("Weather", "weather", ("Clear", "Cloudy", "Rain")),
                                         ("Time", "time_of_day", ("Day", "Dusk", "Night"))):
            tk.Label(settings, text=label).pack(side="left", padx=3)
            selected = tk.StringVar(value=getattr(self.sandbox, variable))
            combo = tk.OptionMenu(settings, selected, *options,
                                  command=lambda value, v=variable: setattr(self.sandbox, v, value))
            combo.configure(width=8)
            combo.pack(side="left")
        for label, attribute in (("Emergencies", "emergencies"), ("Training safety", "training_safety"),
                                 ("Separation warnings", "separation_warnings")):
            target = self.sandbox if attribute == "emergencies" else self.simulation
            var = tk.BooleanVar(value=getattr(target, attribute))
            tk.Checkbutton(settings, text=label, variable=var,
                            command=lambda t=target, a=attribute, v=var: setattr(t, a, v.get())).pack(side="left", padx=3)
        safety_settings = tk.LabelFrame(bar, text="Safety thresholds", padx=3, pady=2)
        safety_settings.pack(fill="x", pady=(3, 0))
        safety = self.simulation.safety
        self.safety_threshold_vars = {
            "horizontal_warning": tk.StringVar(value=f"{safety.horizontal_warning:g}"),
            "horizontal_critical": tk.StringVar(value=f"{safety.horizontal_critical:g}"),
            "vertical_warning": tk.StringVar(value=str(safety.vertical_warning)),
        }
        for label, key, lower, upper, increment, width in (
                ("Warn px", "horizontal_warning", 20, 200, 5, 5),
                ("Critical px", "horizontal_critical", 10, 200, 5, 5),
                ("Vertical ft", "vertical_warning", 500, 3000, 100, 6)):
            tk.Label(safety_settings, text=label).pack(side="left", padx=(7, 2))
            control = tk.Spinbox(safety_settings, from_=lower, to=upper, increment=increment,
                                 textvariable=self.safety_threshold_vars[key], width=width,
                                 command=self._apply_safety_thresholds)
            control.pack(side="left")
            control.bind("<Return>", self._apply_safety_thresholds)
            control.bind("<FocusOut>", self._apply_safety_thresholds)
        tk.Button(safety_settings, text="Defaults", command=self._reset_safety_thresholds).pack(side="left", padx=8)

    def _apply_safety_thresholds(self, event=None):
        variables = self.safety_threshold_vars
        try:
            self.simulation.safety.set_thresholds(variables["horizontal_warning"].get(),
                                                  variables["horizontal_critical"].get(),
                                                  variables["vertical_warning"].get())
        except (ValueError, tk.TclError):
            safety = self.simulation.safety
            variables["horizontal_warning"].set(f"{safety.horizontal_warning:g}")
            variables["horizontal_critical"].set(f"{safety.horizontal_critical:g}")
            variables["vertical_warning"].set(str(safety.vertical_warning))
            messagebox.showwarning("Invalid safety thresholds",
                                   "Use positive values. Critical horizontal distance must not exceed warning distance.")
        self.refresh()

    def _reset_safety_thresholds(self):
        self.simulation.safety.reset_thresholds()
        safety = self.simulation.safety
        self.safety_threshold_vars["horizontal_warning"].set(f"{safety.horizontal_warning:g}")
        self.safety_threshold_vars["horizontal_critical"].set(f"{safety.horizontal_critical:g}")
        self.safety_threshold_vars["vertical_warning"].set(str(safety.vertical_warning))
        self.refresh()

    def spawn_aircraft(self):
        if self.simulation.game_over:
            return
        if self.sandbox.spawn() is None:
            messagebox.showinfo("Aircraft limit reached", f"Additional aircraft cannot be spawned until existing traffic leaves.\n{self.player_name} cannot add more aircraft yet.")

    def remove_selected(self):
        simulation = self.simulation
        callsign = simulation.selected_callsign
        if (simulation.mode != GameMode.SANDBOX or simulation.game_over
                or simulation.get_aircraft(callsign) is None
                or getattr(self, "_delete_confirmation_open", False)):
            return
        self._delete_confirmation_open = True
        was_paused = simulation.paused
        simulation.pause()
        self.refresh()
        try:
            if messagebox.askyesno("LtATC Training Safety",
                                   f"Removing {callsign} will remove this aircraft from the active simulation.\n\nRemove aircraft?",
                                   parent=self.root, default=messagebox.NO):
                simulation.remove_aircraft(callsign)
        finally:
            self._delete_confirmation_open = False
            if not was_paused:
                simulation.resume()
            self.refresh()

    def clear_all(self):
        for callsign in list(self.simulation.aircraft):
            self.simulation.remove_aircraft(callsign)

    def select_aircraft(self, callsign):
        self.simulation.select(callsign)
        if self.simulation.mode == GameMode.STORY and self.story_manager.current:
            self.story_manager.current.handle_event(GameEvent(EventType.AIRCRAFT_SELECTED, callsign))
        lesson = self.lessons.current
        if self.simulation.mode == GameMode.LESSON and lesson:
            lesson.identified = True
        self.refresh()

    def check_runway(self):
        runway = self.simulation.runway
        message = f"Runway {runway.name}: " + (f"occupied by {runway.occupied_by}" if runway.occupied_by else "clear")
        self.dialogue.show("System", message)
        lesson = self.lessons.current
        if self.simulation.mode == GameMode.LESSON and lesson and not runway.occupied_by:
            lesson.runway_checked = True
        if self.simulation.mode == GameMode.STORY and self.story_manager.current and not runway.occupied_by:
            self.story_manager.current.handle_event(GameEvent(EventType.OBJECTIVE_COMPLETED, detail="runway_checked"))
        self.refresh()

    def next_dialogue(self):
        self.dialogue.advance()
        self.refresh()

    def issue_clearance(self, clearance: Clearance):
        if self.simulation.game_over:
            return
        callsign = self.simulation.selected_callsign
        chapter = self.story_manager.current if self.simulation.mode == GameMode.STORY else None
        if self.simulation.mode == GameMode.LESSON and self.lessons.current and self.lessons.current.lesson_id == "01":
            from game.clearances import ClearanceType
            if clearance.clearance_type == ClearanceType.TAKEOFF and not self.lessons.current.runway_checked:
                self.simulation.metrics.clearances_attempted += 1
                self.simulation.metrics.unsafe_clearances_prevented += 1
                show_warning("Check Runway 27 status before transmitting a takeoff clearance.")
                return
        plane = self.simulation.get_aircraft(callsign)
        if chapter and plane:
            story_warning = chapter.validate_clearance(plane, clearance, self.simulation)
            if story_warning:
                self.simulation.metrics.clearances_attempted += 1
                self.simulation.metrics.unsafe_clearances_prevented += 1
                self.story.unsafe_clearances_prevented += 1
                show_warning(story_warning)
                self.dialogue.show("TRAINER01", story_warning)
                return
        result = self.simulation.transmit(callsign, clearance)
        if not result.safe:
            show_warning(result.message + "\n\nClearance was not transmitted. Review the situation and try again.")
            self.dialogue.show("Blaze", result.message)
        else:
            plane = self.simulation.get_aircraft(callsign)
            if self.simulation.mode == GameMode.LESSON and self.lessons.current:
                self.lessons.current.handle_clearance(plane, clearance)
            if chapter:
                chapter.handle_clearance(plane, clearance)
                chapter.handle_event(GameEvent(EventType.CLEARANCE_TRANSMITTED, callsign, clearance.clearance_type.name))
            self.dialogue.show(callsign, f"Roger, {clearance.clearance_type.name.replace('_', ' ').lower()}"
                               + (f" {clearance.value}" if clearance.value is not None else "") + ".")
            if self.simulation.metrics.unsafe_clearances_prevented > self.simulation.metrics.self_corrections:
                self.simulation.metrics.self_corrections += 1
                if chapter:
                    self.story.mistakes_corrected += 1
        self.refresh()

    def retry_story_checkpoint(self):
        chapter = self.story_manager.current
        if chapter:
            chapter.retry_checkpoint(self.simulation, self.story)
            self.story.current_checkpoint = chapter.checkpoint_name
            self.boundary_shown = False
            self.dialogue.show("System", f"Checkpoint restored: {chapter.checkpoint_name}")
            self.refresh()

    def story_action(self, action):
        chapter = self.story_manager.current
        if chapter is None:
            return
        chapter.choose(action, self.simulation, self.story)
        if not chapter.completed:
            self._drain_story_messages()
        self.refresh()

    def _drain_story_messages(self):
        chapter = self.story_manager.current
        if chapter:
            for speaker, message in chapter.drain_messages():
                self.dialogue.show(speaker, message)

    def tick(self):
        now = time.monotonic()
        dt = min(now - self.last_tick, .2)
        self.last_tick = now
        if self.simulation.mode != GameMode.MAIN_MENU:
            # Query Tk directly: focus_get() cannot resolve some native popups
            # (such as option menus) to Python widget objects. An empty
            # focus path means this application no longer has keyboard focus.
            if not self.root.tk.call("focus"):
                self.simulation.pause()
                self.refresh()
                self.root.after(33, self.tick)
                return
            self.simulation.update(dt)
            if self.simulation.game_over:
                self.refresh()
                self.root.after(33, self.tick)
                return
            conflicts = self.simulation.safety.conflicts(list(self.simulation.aircraft.values()))
            if not any(conflict.critical for conflict in conflicts):
                self.boundary_shown = False
            lesson = self.lessons.current if self.simulation.mode == GameMode.LESSON else None
            chapter = self.story_manager.current if self.simulation.mode == GameMode.STORY else None
            if chapter and not self.reported:
                chapter.update(self.simulation, self.story, dt if not self.simulation.paused else 0)
                self.story.current_checkpoint = chapter.checkpoint_name
                if conflicts and any(c.critical for c in conflicts) and self.simulation.training_safety and not self.boundary_shown:
                    self.simulation.pause()
                    self.boundary_shown = True
                    self.story.safety_interventions += 1
                    choice = messagebox.askyesnocancel("Training safety boundary", "TRAINING SAFETY BOUNDARY ACTIVATED\n\nInspect the situation?\nYes: inspect while paused\nNo: retry checkpoint\nCancel: return to story menu")
                    if choice is False:
                        self.retry_story_checkpoint()
                    elif choice is None:
                        self.show_story_menu()
                        self.root.after(33, self.tick)
                        return
                if chapter.check_completion() and not self.reported:
                    self.reported = True
                    self.simulation.pause()
                    if not self.game.complete_chapter(chapter.chapter_id):
                        show_warning("Chapter progress could not be saved. Check that the progress folder is writable, then retry the chapter.")
                        self.root.after(33, self.tick)
                        return
                    reactions = "\n".join(f"{speaker}: {message}" for speaker, message in chapter.drain_messages())
                    ending = "Story Mode complete." if chapter.chapter_id == "04" else "The next chapter is unlocked."
                    messagebox.showinfo("Chapter complete", f"{chapter.title}\n\n{chapter.event_indicator or 'Objective complete'}\n\n{reactions}\n\n{ending}")
                    self.show_story_menu()
                else:
                    self._drain_story_messages()
            if lesson and not self.reported:
                if conflicts and any(c.critical for c in conflicts) and self.simulation.training_safety and not self.boundary_shown:
                    self.simulation.pause()
                    self.boundary_shown = True
                    self.simulation.metrics.instructor_interventions += 1
                    self.story.safety_interventions += 1
                    pair = conflicts[0]
                    retry = messagebox.askretrycancel("Training safety boundary", f"{pair.first} and {pair.second} would lose separation.\nSimulation paused.\n\nRetry from the safe checkpoint?")
                    if retry:
                        self.start_lesson(lesson.lesson_id, restart=True)
                        self.root.after(33, self.tick)
                        return
                    else:
                        self.dialogue.show("Blaze", "Inspect the aircraft, then use Retry when ready.")
                lesson.update(self.simulation)
                if lesson.completed and not self.reported:
                    self.reported = True
                    self.simulation.pause()
                    if not self.game.complete_lesson(lesson.lesson_id):
                        show_warning("Lesson progress could not be saved. Check that the progress folder is writable, then retry the lesson.")
                        self.root.after(33, self.tick)
                        return
                    show_report(lesson, self.simulation.metrics, self.player_name)
                    self.show_lesson_menu()
            if self.simulation.mode != GameMode.MAIN_MENU:
                self.refresh(conflicts if self.simulation.separation_warnings else [])
        self.root.after(33, self.tick)

    def refresh(self, conflicts=None):
        mode = self.simulation.mode
        selected = self.simulation.get_aircraft(self.simulation.selected_callsign)
        player = f"{self.player_name} | " if mode in {GameMode.LESSON, GameMode.SANDBOX} else ""
        mode_text = f"{player}{mode.name}" if player else mode.name
        conflict_text = "GAME OVER" if self.simulation.game_over else "PAUSED" if self.simulation.paused else "NO CONFLICT"
        selection_text = f"{self.simulation.selected_callsign} SELECTED" if self.simulation.selected_callsign else conflict_text
        self._set_status(mode_text, f"{self.simulation.speed:.1f}x",
                         f"SAFETY {'ON' if self.simulation.training_safety else 'OFF'}",
                         f"AIRCRAFT {len(self.simulation.aircraft):02d}/{AIRCRAFT_LIMIT:02d}", selection_text)
        self.menu_safety_var.set(self.simulation.training_safety)
        if mode == GameMode.MAIN_MENU:
            return
        if self.simulation.game_over:
            self.game_over_reason.configure(text=f"GAME OVER: {self.simulation.collision.reason} Retry to start a fresh session.")
            self.game_over_panel.pack(fill="x", before=self.game_body)
        else:
            self.game_over_panel.pack_forget()
        self.radar.refresh(self.simulation, conflicts or [])
        active_lesson = self.lessons.current if mode == GameMode.LESSON else None
        self.lesson_panel.refresh(active_lesson,
                                  self.dialogue.current, self.images, mode.name)
        if mode == GameMode.STORY and self.story_panel:
            self.story_panel.refresh(self.story_manager.current)
        self.aircraft_panel.refresh(selected)
        self.controls.refresh(selected, mode == GameMode.SANDBOX)
