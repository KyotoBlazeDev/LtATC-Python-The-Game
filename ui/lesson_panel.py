import tkinter as tk

class LessonPanel(tk.LabelFrame):
    def __init__(self, parent, on_next, on_runway_check):
        super().__init__(parent, text="Lesson / dialogue", padx=10, pady=10)
        self.training_note = tk.Label(self)
        self.title_label = tk.Label(self, text="Welcome", font=("TkDefaultFont", 12, "bold"))
        self.title_label.pack(anchor="w")
        self.objectives = tk.Label(self, text="Choose a mode to begin.", wraplength=300, justify="left")
        self.objectives.pack(anchor="w", pady=6)
        self.portrait = tk.Label(self)
        self.portrait.pack(anchor="w")
        self.dialogue = tk.Label(self, text="", wraplength=300, justify="left")
        self.dialogue.pack(anchor="w", pady=6)
        row = tk.Frame(self)
        row.pack(fill="x")
        tk.Button(row, text="Next dialogue", command=on_next).pack(side="left")
        tk.Button(row, text="Check Runway 27", command=on_runway_check).pack(side="left", padx=5)

    def refresh(self, lesson, line, portraits, mode="SANDBOX"):
        training_note = portraits.get("training_note") if lesson else None
        if training_note:
            self.training_note.configure(image=training_note)
            self.training_note.image = training_note
            self.training_note.pack(anchor="w", pady=(0, 6), before=self.title_label)
        else:
            self.training_note.pack_forget()
            self.training_note.configure(image="")
            self.training_note.image = None
        self.title_label.configure(text=lesson.title if lesson else ("Story dialogue" if mode == "STORY" else "Sandbox training"))
        if lesson:
            self.objectives.configure(text="\n".join(f"• {item}" for item in lesson.objectives))
        else:
            self.objectives.configure(text="Follow the current story objective." if mode == "STORY" else
                                      "Explore clearances. Safety warnings remain available.")
        self.dialogue.configure(text=f"{line.speaker}: {line.message}" if line else "")
        image = portraits.get(line.speaker) if line else None
        self.portrait.configure(image=image or "")
        self.portrait.image = image
