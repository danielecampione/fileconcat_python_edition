# main.py
import tkinter as tk
from gui import MergeGUI

def main():
    root = tk.Tk()
    app = MergeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
