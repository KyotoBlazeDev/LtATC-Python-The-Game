import tkinter as tk
from game.aircraft import AircraftState
from game.clearances import Clearance, ClearanceType

class ControlPanel(tk.LabelFrame):
    def __init__(self, parent, on_clearance):
        super().__init__(parent, text="Clearances", padx=8, pady=8)
        self.on_clearance = on_clearance
        self.buttons = {}
        for i, (label, kind) in enumerate((("Takeoff", ClearanceType.TAKEOFF), ("Heading", ClearanceType.HEADING),
                                           ("Altitude", ClearanceType.ALTITUDE), ("Speed", ClearanceType.SPEED),
                                           ("Approach", ClearanceType.APPROACH), ("Land", ClearanceType.LAND),
                                           ("Hold", ClearanceType.HOLD), ("Line up", ClearanceType.LINE_UP_AND_WAIT),
                                           ("Go around", ClearanceType.GO_AROUND))):
            button = tk.Button(self, text=label, command=lambda k=kind: self._choose(k))
            button.grid(row=i//3, column=i%3, sticky="ew", padx=2, pady=2)
            self.buttons[kind] = button
        for col in range(3):
            self.columnconfigure(col, weight=1)
        self.options = tk.Frame(self)
        self.options.grid(row=3, column=0, columnspan=3, sticky="ew")
        for col in range(3):
            self.options.columnconfigure(col, weight=1)

    def _choose(self, kind):
        for child in self.options.winfo_children():
            child.destroy()
        values = {ClearanceType.HEADING: (90, 120, 150, 180, 210, 240, 270, 300, 330),
                  ClearanceType.ALTITUDE: (1000, 2000, 3000, 4000, 5000),
                  ClearanceType.SPEED: (70, 90, 110, 130)}.get(kind)
        if values is None:
            self.on_clearance(Clearance(kind))
            return
        for i, value in enumerate(values):
            tk.Button(self.options, text=str(value), command=lambda v=value: self.on_clearance(Clearance(kind, v))).grid(
                row=i//3, column=i%3, padx=1, pady=2, sticky="ew")

    def refresh(self, plane, sandbox=False):
        ground = {AircraftState.PARKED, AircraftState.HOLDING_SHORT, AircraftState.LINE_UP, AircraftState.LANDED}
        for kind, button in self.buttons.items():
            enabled = plane is not None
            if plane and not sandbox:
                if kind in {ClearanceType.TAKEOFF, ClearanceType.LINE_UP_AND_WAIT}:
                    enabled = plane.state in ground
                elif kind in {ClearanceType.LAND, ClearanceType.APPROACH, ClearanceType.HEADING,
                              ClearanceType.ALTITUDE, ClearanceType.SPEED}:
                    enabled = plane.state not in ground
            button.configure(state="normal" if enabled else "disabled")
