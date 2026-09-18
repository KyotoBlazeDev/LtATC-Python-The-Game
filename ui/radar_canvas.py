import tkinter as tk
import tkinter.font as tkfont
import time
from math import cos, radians, sin

class RadarCanvas(tk.Canvas):
    LOGICAL_WIDTH = 700
    LOGICAL_HEIGHT = 590

    @classmethod
    def screen_position(cls, x, y, width, height):
        return x * width / cls.LOGICAL_WIDTH, y * height / cls.LOGICAL_HEIGHT

    def __init__(self, parent, on_select, plane_image=None, selected_frame=None,
                 unselected_frame=None, paused_image=None, critical_image=None,
                 separation_warning_frame=None, separation_critical_frame=None,
                 directional_prompt=None, separation_warning_image=None, explosion_image=None):
        super().__init__(parent, bg="#101e23", highlightthickness=0, width=700, height=590)
        self.on_select = on_select
        self.plane_image = plane_image
        self.selected_frame = selected_frame
        self.unselected_frame = unselected_frame
        self.paused_image = paused_image
        self.critical_image = critical_image
        self.separation_warning_frame = separation_warning_frame
        self.separation_critical_frame = separation_critical_frame
        self.directional_prompt = directional_prompt
        self.separation_warning_image = separation_warning_image
        self.explosion_image = explosion_image
        self.bind("<Button-1>", self._click)
        self.positions = {}
        self.teletext = False
        self.dos = False
        self.teletext_page = 100
        self.teletext_family = "Bedstead" if "Bedstead" in tkfont.families(parent) else "Consolas"

    def set_teletext(self, enabled, family=None):
        self.teletext = enabled
        self.dos = False
        if family:
            self.teletext_family = family
        self.configure(bg="#050505" if enabled else "#101e23")

    def set_teletext_page(self, page):
        if page in (100, 101, 102, 103):
            self.teletext_page = page

    def set_dos(self, enabled):
        self.dos = enabled
        self.teletext = False
        self.configure(bg="#0000aa" if enabled else "#101e23")

    def _click(self, event):
        # Classic Tk widgets do not consistently transfer keyboard focus to a
        # canvas on click. Keep global aircraft shortcuts active after radar use.
        self.focus_force()
        hit_x = self.winfo_width() / (160 if self.dos else 80) if self.teletext or self.dos else 24
        hit_y = self.winfo_height() / 50 if self.teletext or self.dos else 24
        for callsign, (x, y) in reversed(list(self.positions.items())):
            if abs(event.x - x) <= hit_x and abs(event.y - y) <= hit_y:
                self.on_select(callsign)
                return

    def refresh(self, simulation, conflicts=()):
        self.delete("all")
        if self.dos:
            self._refresh_dos(simulation, conflicts)
            self._draw_game_over(simulation)
            return
        if self.teletext:
            self._refresh_teletext(simulation, conflicts)
            self._draw_game_over(simulation)
            return
        width, height = self.winfo_width(), self.winfo_height()
        scale_x, scale_y = width / self.LOGICAL_WIDTH, height / self.LOGICAL_HEIGHT
        def screen(x, y):
            return self.screen_position(x, y, width, height)
        for radius in (80, 160, 240):
            self.create_oval(width/2-radius, height/2-radius, width/2+radius, height/2+radius, outline="#274b4b")
        self.create_line(width/2, 0, width/2, height, fill="#274b4b")
        self.create_line(0, height/2, width, height/2, fill="#274b4b")
        r = simulation.runway
        start_x, start_y = screen(r.start_x, r.start_y)
        end_x, end_y = screen(r.end_x, r.end_y)
        self.create_line(start_x, start_y, end_x, end_y, fill="#c9d0cb", width=13)
        self.create_line(start_x, start_y, end_x, end_y, fill="#333d3e", width=9)
        self.create_text(end_x-8, end_y-20, text=f"RWY {r.name}", fill="#e9f0d2", anchor="e")
        self.positions = {}
        conflicted = {name for item in conflicts for name in (item.first, item.second)}
        critical = {name for item in conflicts if item.critical for name in (item.first, item.second)}
        for index, plane in enumerate(simulation.aircraft.values(), 1):
            x, y = screen(plane.x, plane.y)
            self.positions[plane.callsign] = (x, y)
            color = ("#ff202b" if plane.callsign in critical else
                     "#fff200" if plane.callsign in conflicted else "#82e9ca")
            if plane.callsign in critical:
                frame = self.separation_critical_frame
            elif plane.callsign in conflicted:
                frame = self.separation_warning_frame
            else:
                frame = self.selected_frame if plane.selected else self.unselected_frame
            if frame:
                self.create_image(x, y, image=frame)
            elif plane.selected:
                self.create_oval(x-17, y-17, x+17, y+17, outline="#fff3a4", width=2)
            if plane.callsign in conflicted and not frame:
                self.create_oval(x-26, y-26, x+26, y+26, outline=color, width=2)
            h = radians(plane.heading)
            self.create_line(x, y, x+sin(h)*32*scale_x, y-cos(h)*32*scale_y, fill=color, width=2)
            if self.plane_image:
                self.create_image(x, y, image=self.plane_image)
            else:
                self.create_oval(x-5, y-5, x+5, y+5, fill=color)
            label_x, anchor = (x-12, "se") if x > width-140 else (x+12, "sw")
            number = f"{index}. " if index <= 9 else ""
            self.create_text(label_x, y-12, text=f"{number}{plane.callsign}\n{plane.altitude} ft  {round(plane.heading):03d}°",
                             fill=color, anchor=anchor, font=("Fixedsys", 9, "bold"))
        selected = simulation.get_aircraft(simulation.selected_callsign)
        if selected is not None:
            x, y = self.positions[selected.callsign]
            # Ease the prompt toward the target and back once per second.
            phase = (time.monotonic() % 1.0) * 2
            bob = (1 - abs(phase - 1)) * 8
            prompt_x = max(10, x - 22 - bob)
            if self.directional_prompt:
                self.create_image(prompt_x, y, image=self.directional_prompt, anchor="e")
            else:
                self.create_polygon(prompt_x-22, y-9, prompt_x-22, y+9, prompt_x, y,
                                    fill="#82e9ca", outline="")
        if conflicts:
            pair = conflicts[0]
            warning_color = "#ff202b" if pair.critical else "#fff200"
            if self.separation_warning_image and not pair.critical:
                self.create_image(width / 2, 8, image=self.separation_warning_image, anchor="n")
                self.create_text(width / 2, 72, text=f"{pair.first} / {pair.second}",
                                 fill=warning_color, anchor="n", font=("Fixedsys", 11, "bold"))
            else:
                self.create_text(12, 12, text=f"SEPARATION WARNING: {pair.first} / {pair.second}",
                                 fill=warning_color, anchor="nw", font=("Fixedsys", 11, "bold"))
        if any(conflict.critical for conflict in conflicts) and int(time.monotonic() * 2) % 2 == 0:
            if self.critical_image:
                self.create_image(width / 2, 60, image=self.critical_image, anchor="n")
            else:
                self.create_text(width / 2, 60, text="CRITICAL! SAFETY MODE ON", fill="#ff2222",
                                 anchor="n", font=("Fixedsys", 18, "bold"))
        if simulation.paused and not simulation.game_over:
            # A compact corner annunciator keeps aircraft labels and the
            # runway visible while still making the held state unmistakable.
            self.create_rectangle(10, 10, 112, 42, fill="#202020", outline="#ffc90e", width=2)
            self.create_text(61, 26, text="PAUSED", fill="#ffc90e",
                             font=("Fixedsys", 13, "bold"))
        self._draw_game_over(simulation)

    def _draw_game_over(self, simulation):
        if not simulation.game_over:
            return
        width, height = self.winfo_width(), self.winfo_height()
        impact = simulation.collision
        if not self.teletext and not self.dos:
            x, y = self.screen_position(impact.x, impact.y, width, height)
            if self.explosion_image:
                self.create_image(x, y, image=self.explosion_image, tags="collision")
            else:
                self.create_text(x, y, text="✹", fill="#ff9020",
                                 font=("Fixedsys", 48, "bold"), tags="collision")
        self.create_rectangle(0, 0, width, 38, fill="#501414", outline="", tags="game_over")
        self.create_text(width / 2, 19, text="GAME OVER — COLLISION", fill="#ffffff",
                         font=("Fixedsys", 16, "bold"), tags="game_over")

    def _refresh_teletext(self, simulation, conflicts):
        """Draw a 40-column, 25-row character display over the game coordinates."""
        width, height = max(self.winfo_width(), 1), max(self.winfo_height(), 1)
        cell_w, cell_h = width / 40, height / 25
        size = max(8, min(int(cell_h * .75), int(cell_w * 1.35)))
        face = (self.teletext_family, size)
        cyan, yellow, white, red = "#00ffff", "#ffff00", "#ffffff", "#ff0000"
        green, blue = "#00ff00", "#0000ff"

        def put(col, row, value, color=white):
            self.create_text((col + .5) * cell_w, (row + .5) * cell_h,
                             text=str(value)[:40-col], anchor="center" if len(str(value)) == 1 else "w",
                             fill=color, font=face)

        self.create_rectangle(0, 0, width, cell_h, fill=blue, outline="")
        self.create_rectangle(0, cell_h, width, cell_h * 2, fill="#001060", outline="")
        page_titles = {100: "RADAR", 101: "TRAFFIC", 102: "RUNWAY", 103: "ALERTS"}
        page = self.teletext_page
        put(0, 0, f"P{page} LTATC {page_titles[page]:<12} {time.strftime('%H:%M')}", white)
        put(0, 1, f"{simulation.mode.name:<8}  RWY {simulation.runway.name:<3}  {len(simulation.aircraft):02d} TARGETS  {'HOLD' if simulation.paused else 'LIVE'}", cyan)
        put(0, 2, "=" * 40, yellow)
        if page != 100:
            self.positions = {}
            self._refresh_teletext_info(simulation, conflicts, page, put, cell_w, cell_h, white, cyan, yellow, red, green, blue)
            return
        put(1, 3, "N", green)
        put(34, 3, "LIVE" if not simulation.paused else "HOLD", green if not simulation.paused else yellow)
        for row in range(5, 18, 4):
            for col in range(5, 39, 6):
                put(col, row, "+", "#005050")
        for row in range(3, 19):
            put(0, row, "|", green)
            put(39, row, "|", green)
        put(0, 19, "+" + "-" * 38 + "+", green)

        def grid(x, y):
            return (max(1, min(38, round(x / self.LOGICAL_WIDTH * 37) + 1)),
                    max(3, min(18, round(y / self.LOGICAL_HEIGHT * 15) + 3)))

        runway = simulation.runway
        for step in range(21):
            x = runway.start_x + (runway.end_x - runway.start_x) * step / 20
            y = runway.start_y + (runway.end_y - runway.start_y) * step / 20
            col, row = grid(x, y)
            put(col, row, "\u2588", yellow)
        put(2, 18, "RWY " + runway.name, yellow)

        self.positions = {}
        conflicted = {name for item in conflicts for name in (item.first, item.second)}
        for index, plane in enumerate(simulation.aircraft.values(), 1):
            col, row = grid(plane.x, plane.y)
            color = red if plane.callsign in conflicted else yellow if plane.selected else green
            put(col, row, "X" if plane.callsign in conflicted else "\u25a0" if plane.selected else "\u25cf", color)
            self.positions[plane.callsign] = ((col + .5) * cell_w, (row + .5) * cell_h)
            if index <= 4:
                put(1, 19 + index,
                    f"{index} {plane.callsign[:12]:12} {plane.altitude:5}FT {round(plane.heading):03d}D", color)
        if not simulation.aircraft:
            put(1, 20, "NO TRAFFIC IN CONTROL AREA", cyan)
        if conflicts:
            pair = conflicts[0]
            self.create_rectangle(0, 24 * cell_h, width, height, fill="#770000", outline="")
            put(1, 24, f"WARNING {pair.first} / {pair.second}", white)
        else:
            for left, right, color in ((0, 10, red), (10, 20, green), (20, 30, yellow), (30, 40, blue)):
                self.create_rectangle(left * cell_w, 24 * cell_h, right * cell_w, height, fill=color, outline="")
            put(1, 24, "TAB SELECT", white)
            put(12, 24, "1-9 TARGET", "#000000")
            put(22, 24, "0 CLEAR", "#000000")
            put(32, 24, "P100", white)

    def _refresh_teletext_info(self, simulation, conflicts, page, put,
                               cell_w, cell_h, white, cyan, yellow, red, green, blue):
        if page == 101:
            put(1, 3, "TRAFFIC INDEX", yellow)
            put(1, 4, "NO CALLSIGN    ALT", cyan)
            put(21, 4, "NO CALLSIGN    ALT", cyan)
            for index, plane in enumerate(simulation.aircraft.values(), 1):
                column = 1 if index <= 16 else 21
                row = 4 + index if index <= 16 else index - 12
                color = yellow if plane.selected else green
                put(column, row, f"{index:02d} {plane.callsign[:10]:10} {plane.altitude:5}", color)
            if not simulation.aircraft:
                put(1, 6, "NO AIRCRAFT IN CONTROL AREA", green)
            put(1, 22, "@ SELECTED   X SEPARATION WARNING", yellow)
        elif page == 102:
            runway = simulation.runway
            put(1, 3, "RUNWAY STATUS", yellow)
            put(1, 5, f"RUNWAY         {runway.name}", white)
            put(1, 7, f"OCCUPANCY      {runway.occupied_by or 'CLEAR'}", green if not runway.occupied_by else red)
            put(1, 9, "-------------------------------", cyan)
            selected = simulation.get_aircraft(simulation.selected_callsign)
            if selected:
                put(1, 11, "SELECTED AIRCRAFT", yellow)
                put(1, 13, f"CALLSIGN       {selected.callsign}", white)
                put(1, 15, f"ALTITUDE       {selected.altitude} FT", white)
                put(1, 17, f"HEADING        {round(selected.heading):03d} DEG", white)
            else:
                put(1, 12, "SELECT AN AIRCRAFT FOR DETAILS", cyan)
            put(1, 22, "USE CHECK RUNWAY FOR GAME ACTION", yellow)
        else:
            put(1, 3, "SEPARATION ALERTS", yellow)
            if conflicts:
                for index, pair in enumerate(conflicts[:14], 1):
                    put(1, index + 4, f"{index:02d} {pair.first[:14]:14} / {pair.second[:14]}", red if pair.critical else yellow)
                if len(conflicts) > 14:
                    put(1, 20, f"+{len(conflicts)-14} MORE ALERTS", yellow)
            elif not simulation.separation_warnings:
                put(1, 6, "SEPARATION WARNINGS DISABLED", yellow)
            else:
                put(1, 6, "NO CURRENT SEPARATION ALERTS", green)
            put(1, 22, "ALERTS REFRESH WITH SIMULATION", cyan)
        put(0, 23, "=" * 40, yellow)
        for left, right, color in ((0, 10, red), (10, 20, green), (20, 30, yellow), (30, 40, blue)):
            self.create_rectangle(left * cell_w, 24 * cell_h, right * cell_w, 25 * cell_h,
                                  fill=color, outline="")
        put(1, 24, "100 RADAR", white)
        put(11, 24, "101 TRAFFIC", "#000000")
        put(21, 24, "102 RUNWAY", "#000000")
        put(31, 24, "103 ALERTS", white)

    def _refresh_dos(self, simulation, conflicts):
        """Draw an 80 x 25 DOS-style tactical screen."""
        width, height = max(self.winfo_width(), 1), max(self.winfo_height(), 1)
        cell_w, cell_h = width / 80, height / 25
        size = max(7, min(int(cell_h * .72), int(cell_w * 1.55)))
        family = "Modern DOS 8x16" if "Modern DOS 8x16" in tkfont.families(self) else "Consolas"
        face = (family, size)
        white, cyan, yellow, red = "#dddddd", "#55ffff", "#ffff55", "#ff5555"

        def put(col, row, value, color=white):
            value = str(value)[:80-col]
            self.create_text((col + .5) * cell_w, (row + .5) * cell_h, text=value,
                             anchor="center" if len(value) == 1 else "w", fill=color, font=face)

        put(0, 0, " LtATC DOS MODE  |  TACTICAL AIRCRAFT DISPLAY ".ljust(80, "="), white)
        put(0, 1, f" MODE {simulation.mode.name:<8}  TRAFFIC {len(simulation.aircraft):02d}  RWY {simulation.runway.name:<5}  STATUS {'PAUSED' if simulation.paused else 'ACTIVE'}", cyan)
        put(0, 2, "+" + "-" * 52 + "+" + "-" * 25 + "+", white)
        for row in range(3, 22):
            put(0, row, "|", white)
            put(53, row, "|", white)
            put(79, row, "|", white)
        put(0, 22, "+" + "-" * 52 + "+" + "-" * 25 + "+", white)
        put(56, 3, "NO CALLSIGN    ALT HDG", yellow)

        def grid(x, y):
            return (max(1, min(52, round(x / self.LOGICAL_WIDTH * 51) + 1)),
                    max(3, min(21, round(y / self.LOGICAL_HEIGHT * 18) + 3)))

        runway = simulation.runway
        for step in range(26):
            x = runway.start_x + (runway.end_x - runway.start_x) * step / 25
            y = runway.start_y + (runway.end_y - runway.start_y) * step / 25
            col, row = grid(x, y)
            put(col, row, "=", yellow)

        self.positions = {}
        conflicted = {name for item in conflicts for name in (item.first, item.second)}
        for index, plane in enumerate(simulation.aircraft.values(), 1):
            col, row = grid(plane.x, plane.y)
            color = red if plane.callsign in conflicted else yellow if plane.selected else cyan
            put(col, row, "X" if plane.callsign in conflicted else "@" if plane.selected else str(index % 10), color)
            self.positions[plane.callsign] = ((col + .5) * cell_w, (row + .5) * cell_h)
            if index <= 17:
                put(56, index + 3, f"{index:02d} {plane.callsign[:10]:10} {plane.altitude:5} {round(plane.heading):03d}", color)
        put(0, 23, " TAB / SHIFT+TAB SELECT   1-9 TARGET   0 CLEAR", white)
        if conflicts:
            pair = conflicts[0]
            put(0, 24, f" ! SEPARATION WARNING: {pair.first} / {pair.second}", red)
        else:
            put(0, 24, " READY. SELECT AN AIRCRAFT TO ISSUE A CLEARANCE.", cyan)
