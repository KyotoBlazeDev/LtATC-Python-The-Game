"""Story-specific objective and decision controls."""
import webbrowser
import tkinter as tk

class StoryPanel(tk.LabelFrame):
    def __init__(self, parent, on_action):
        super().__init__(parent, text="Story objective", padx=8, pady=8)
        self.on_action = on_action
        self.title = tk.Label(self, font="LtATCTitleFont", wraplength=300)
        self.title.pack(anchor="w")
        self.objective = tk.Label(self, wraplength=300, justify="left")
        self.objective.pack(anchor="w", pady=4)
        self.event = tk.Label(self, wraplength=300, justify="left")
        self.event.pack(anchor="w", pady=3)
        self.source = tk.Label(self, wraplength=300)
        self.source.pack(anchor="w", pady=3)
        self.source_button = tk.Button(self, text="Open NTSB report")
        self.source_button.pack(anchor="w", pady=2)
        self.checkpoint = tk.Label(self, wraplength=300)
        self.checkpoint.pack(anchor="w", pady=3)
        self.actions = tk.Frame(self)
        self.actions.pack(fill="x")
        self._shown_options = None

    def refresh(self, chapter):
        self.title.configure(text=chapter.title)
        self.objective.configure(text="CURRENT OBJECTIVE\n" + chapter.objective)
        self.event.configure(text=chapter.event_indicator)
        self.source.configure(text="SOURCE: NTSB " + chapter.source_id)
        self.source_button.configure(command=lambda url=chapter.source_url: webbrowser.open(url))
        self.checkpoint.configure(text="CHECKPOINT: " + chapter.checkpoint_name)
        options = chapter.available_actions() if not chapter.completed else ()
        if options != self._shown_options:
            for child in self.actions.winfo_children():
                child.destroy()
            for i, (label, action) in enumerate(options):
                tk.Button(self.actions, text=label, command=lambda a=action: self.on_action(a)).grid(
                    row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
            for i in range(2):
                self.actions.columnconfigure(i, weight=1)
            self._shown_options = options
