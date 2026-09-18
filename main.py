"""Launch LtATC: Python The Game with `python main.py`."""
import logging
import tkinter as tk
from ui.main_window import MainWindow

def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
