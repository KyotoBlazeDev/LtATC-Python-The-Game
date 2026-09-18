import tkinter as tk

class AircraftPanel(tk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Aircraft information", padx=10, pady=10)
        self.label = tk.Label(self, text="Select an aircraft on radar", justify="left", font="LtATCFixedFont")
        self.label.pack(anchor="w", fill="x")

    def refresh(self, plane):
        if plane is None:
            self.label.configure(text="Select an aircraft on radar")
        else:
            self.label.configure(text=f"{plane.callsign}  |  {plane.state.name.replace('_', ' ')}\n"
                                      f"ALT {plane.altitude:5d} ft    HDG {round(plane.heading):03d}°\n"
                                      f"SPD {round(plane.speed):3d} kt    TARGET {round(plane.target_heading):03d}°")
