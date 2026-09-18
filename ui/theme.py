"""Windows 95-inspired visual defaults for the Tk interface."""

import tkinter as tk
import tkinter.font as tkfont


CLASSIC_GRAY = "#c0c0c0"
CLASSIC_DARK = "#808080"
CLASSIC_LIGHT = "#ffffff"
CLASSIC_BLACK = "#000000"
CLASSIC_BLUE = "#000080"
DESKTOP_TEAL = "#008080"


def _first_available(root: tk.Misc, *families: str) -> str:
    available = {family.casefold(): family for family in tkfont.families(root)}
    for family in families:
        if family.casefold() in available:
            return available[family.casefold()]
    return "TkDefaultFont"


def apply_classic_theme(root: tk.Tk) -> None:
    """Apply one coherent Win95-era option database before widgets are built."""
    ui_family = _first_available(root, "MS Sans Serif", "Microsoft Sans Serif", "Arial")
    fixed_family = _first_available(root, "Fixedsys", "Bedstead", "Consolas", "Courier New")

    named_fonts = {
        "TkDefaultFont": (ui_family, 8, "normal"),
        "TkTextFont": (ui_family, 8, "normal"),
        "TkMenuFont": (ui_family, 8, "normal"),
        "TkCaptionFont": (ui_family, 8, "bold"),
        "TkSmallCaptionFont": (ui_family, 8, "normal"),
        "TkFixedFont": (fixed_family, 9, "normal"),
        "LtATCTitleFont": (ui_family, 10, "bold"),
        "LtATCFixedFont": (fixed_family, 9, "normal"),
    }
    for name, (family, size, weight) in named_fonts.items():
        try:
            font = tkfont.nametofont(name, root=root)
        except tk.TclError:
            font = tkfont.Font(root=root, name=name, exists=False)
        font.configure(family=family, size=size, weight=weight)

    root.configure(background=CLASSIC_GRAY)
    root.option_add("*background", CLASSIC_GRAY)
    root.option_add("*foreground", CLASSIC_BLACK)
    root.option_add("*activeBackground", CLASSIC_BLUE)
    root.option_add("*activeForeground", CLASSIC_LIGHT)
    root.option_add("*selectBackground", CLASSIC_BLUE)
    root.option_add("*selectForeground", CLASSIC_LIGHT)
    root.option_add("*highlightBackground", CLASSIC_GRAY)
    root.option_add("*highlightColor", CLASSIC_BLACK)
    root.option_add("*Font", "TkDefaultFont")

    root.option_add("*Button.borderWidth", 2)
    root.option_add("*Button.relief", "raised")
    root.option_add("*Button.padX", 6)
    root.option_add("*Button.padY", 2)
    root.option_add("*Button.highlightThickness", 1)
    root.option_add("*Button.disabledForeground", CLASSIC_DARK)
    root.option_add("*Entry.background", CLASSIC_LIGHT)
    root.option_add("*Entry.relief", "sunken")
    root.option_add("*Entry.borderWidth", 2)
    root.option_add("*Spinbox.background", CLASSIC_LIGHT)
    root.option_add("*Listbox.background", CLASSIC_LIGHT)
    root.option_add("*Text.background", CLASSIC_LIGHT)
    root.option_add("*Menu.background", CLASSIC_GRAY)
    root.option_add("*Menu.foreground", CLASSIC_BLACK)
    root.option_add("*Menu.activeBackground", CLASSIC_BLUE)
    root.option_add("*Menu.activeForeground", CLASSIC_LIGHT)
    root.option_add("*Menu.borderWidth", 2)
    root.option_add("*Menu.relief", "raised")
    root.option_add("*Menubutton.relief", "raised")
    root.option_add("*Scrollbar.troughColor", CLASSIC_GRAY)
    root.option_add("*Scrollbar.background", CLASSIC_GRAY)


def classic_title_bar(parent: tk.Misc, text: str) -> tk.Label:
    """Return a reusable active-window title strip."""
    return tk.Label(
        parent,
        text=text,
        anchor="w",
        background=CLASSIC_BLUE,
        foreground=CLASSIC_LIGHT,
        font="LtATCTitleFont",
        padx=4,
        pady=2,
    )
