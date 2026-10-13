import tkinter as tk

class AircraftPanel(tk.LabelFrame):
    def __init__(self, parent, on_select=None):
        super().__init__(parent, text="Flight strip", padx=10, pady=6)
        self.label = tk.Label(self, text="Select an aircraft on radar", justify="left", font="LtATCFixedFont")
        self.label.pack(anchor="w", fill="x")
        self.on_select = on_select
        self.strips = {}
        self.traffic_title = tk.Label(self, text="Traffic strips (0)", anchor="w")
        self.traffic_title.pack(fill="x", pady=(6, 2))
        container = tk.Frame(self)
        container.pack(fill="x")
        self.canvas = tk.Canvas(container, height=180, width=1, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.rows = tk.Frame(self.canvas)
        row_window = self.canvas.create_window(0, 0, window=self.rows, anchor="nw")
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(row_window, width=event.width))
        self.rows.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.empty = tk.Label(self.rows, text="No active aircraft", anchor="w")

    def refresh(self, plane, aircraft=()):
        if plane is None:
            self.label.configure(text="Select an aircraft on radar")
        else:
            self.label.configure(text=f"{plane.callsign}{' PRIORITY' if plane.emergency else ''}  |  {plane.state.name.replace('_', ' ')}\n"
                                      f"ALT {plane.altitude:5d} ft    HDG {round(plane.heading):03d}°\n"
                                      f"SPD {round(plane.speed):3d} kt    TARGET {round(plane.target_heading):03d}°\n"
                                      f"ASSIGNED ALT {plane.target_altitude} ft  SPD {round(plane.target_speed)} kt\n"
                                      f"DEST {plane.destination or 'Scenario objective'}")
        traffic = list(aircraft)
        callsigns = {item.callsign for item in traffic}
        for callsign in list(self.strips):
            if callsign not in callsigns:
                self.strips.pop(callsign).destroy()
        self.traffic_title.configure(text=f"Traffic strips ({len(traffic)})")
        self.empty.pack_forget()
        if not traffic:
            self.empty.pack(fill="x")
        for item in traffic:
            button = self.strips.get(item.callsign)
            if button is None:
                button = tk.Button(self.rows, anchor="w", justify="left", font="LtATCFixedFont",
                                   command=lambda callsign=item.callsign: self.on_select(callsign) if self.on_select else None)
                button.pack(fill="x", pady=1)
                self.strips[item.callsign] = button
            selected = plane is not None and plane.callsign == item.callsign
            button.configure(text=f"{item.callsign}{' PRIORITY' if item.emergency else ''} | {item.destination or 'Objective'}\n"
                                  f"{item.state.name.replace('_', ' ')}\n"
                                  f"SET {item.target_altitude} ft / {round(item.target_heading):03d}° / {round(item.target_speed)} kt",
                             background="#000080" if selected else "#c0c0c0",
                             foreground="#ffffff" if selected else "#a00000" if item.emergency else "#000000",
                             relief="sunken" if selected else "raised")
