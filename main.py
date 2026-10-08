"""Launch LtATC: Python The Game with `python main.py`."""
import logging
import argparse
import tkinter as tk
from ui.main_window import MainWindow

def main() -> None:
    parser = argparse.ArgumentParser(description="LtATC: Python The Game")
    parser.add_argument("--smoke-test", metavar="REPORT", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.smoke_test:
        from release_smoke import run_smoke_test
        raise SystemExit(run_smoke_test(args.smoke_test))
    logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
