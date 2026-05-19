# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from business_logic import merge_files

EXTENSIONS = [
    "txt", "md", "java", "c", "cpp",
    "html", "htm", "js", "css", "xml"
]

class MergeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unisci File di Testo")
        self.root.geometry("420x500")
        self.root.configure(bg="white")

        self.folder_var = tk.StringVar()
        self.ext_vars = {}

        self.build_ui()

    def build_ui(self):
        title = tk.Label(self.root, text="Unisci file di testo da sottocartelle",
                         font=("Arial", 14, "bold"), bg="white")
        title.pack(pady=10)

        frame_folder = tk.Frame(self.root, bg="white")
        frame_folder.pack(pady=5)

        tk.Label(frame_folder, text="Cartella di partenza:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_folder, textvariable=self.folder_var, width=35).grid(row=1, column=0, padx=5)
        tk.Button(frame_folder, text="Sfoglia", command=self.choose_folder).grid(row=1, column=1, padx=5)

        ext_frame = tk.LabelFrame(self.root, text="Estensioni da includere", bg="white")
        ext_frame.pack(pady=15)

        row = 0
        col = 0
        for ext in EXTENSIONS:
            var = tk.IntVar(value=1 if ext in ["txt", "md"] else 0)
            self.ext_vars[ext] = var
            cb = tk.Checkbutton(ext_frame, text=ext, variable=var, bg="white")
            cb.grid(row=row, column=col, sticky="w", padx=10, pady=3)
            col += 1
            if col == 3:
                col = 0
                row += 1

        tk.Button(self.root, text="Genera output.txt", command=self.generate_output,
                  bg="#e0e0e0", font=("Arial", 12)).pack(pady=20)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def generate_output(self):
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showerror("Errore", "Seleziona una cartella di partenza.")
            return

        selected_exts = [ext for ext, var in self.ext_vars.items() if var.get() == 1]
        if not selected_exts:
            messagebox.showerror("Errore", "Seleziona almeno un'estensione.")
            return

        try:
            output_path = merge_files(folder, selected_exts)
            messagebox.showinfo("Fatto!", f"File generato:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Errore", str(e))
