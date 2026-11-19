"""Create Tk roots for GUI tests."""

import sys
import tkinter as tk
from time import sleep


def create_test_root():
    try:
        return tk.Tk()
    except tk.TclError as error:
        message = str(error)
        library_load_failed = message.startswith(
            ("Can't find a usable init.tcl", "Can't find a usable tk.tcl")
        ) and "couldn't read file" in message
        missing_loader = message == 'invalid command name "tcl_findLibrary"'
        if sys.platform != "win32" or not (library_load_failed or missing_loader):
            raise
        # Hosted Windows runners can intermittently fail to read Tcl/Tk scripts.
        sleep(0.1)
        return tk.Tk()
