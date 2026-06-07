# main.py
try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

import tkinter as tk
from gui import MergeGUI


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = MergeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
