# gui.py
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

from business_logic import merge_files, merge_file_list


# Le estensioni gia note mantengono lo stato predefinito della versione precedente.
KNOWN_EXTENSIONS = {
    "html", "htm", "css", "scss", "sass", "less",
    "js", "mjs", "cjs", "jsx",
    "ts", "tsx", "d.ts",
    "svelte",
    "rs", "toml",
    "py", "pyw", "pyi",
    "c", "h", "cpp", "cc", "cxx", "hpp", "hxx", "cs",
    "java", "kt", "kts", "scala",
    "go", "swift", "dart",
    "rb", "php", "lua",
    "sh", "bash", "zsh", "fish", "ps1",
    "env", "cfg", "ini", "conf",
    "json", "json5", "jsonc", "yaml", "yml",
    "xml", "csv", "sql",
    "md", "mdx", "txt", "rst", "adoc",
    "dockerfile", "makefile", "ninja", "cmake",
    "gradle", "tf", "hcl",
}

DEFAULT_ON = {
    "py", "pyw", "pyi",
    "rs", "toml",
    "ts", "tsx",
    "svelte",
    "js", "mjs", "jsx",
    "html", "css", "scss",
    "md", "txt",
    "json", "yaml", "yml",
}


# ---------------------------------------------------------------------------
# Palette - light, clean, professional
# ---------------------------------------------------------------------------
BG = "#f5f5f5"
BG_WHITE = "#ffffff"
BG_SECTION = "#efefef"
BORDER = "#d0d0d0"
TEXT = "#222222"
TEXT_MUTED = "#888888"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
BTN_BG = "#ffffff"
BTN_BORDER = "#c0c0c0"
BTN_DANGER = "#dc2626"
BTN_DANGER_H = "#b91c1c"
BTN_OK_BG = "#2563eb"
BTN_OK_FG = "#ffffff"
GROUP_FG = "#555555"


try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False


def _btn(parent, text, command, fg=TEXT, bg=BTN_BG, bold=False, **kw):
    f = ("Segoe UI", 9, "bold") if bold else ("Segoe UI", 9)
    button = tk.Button(
        parent,
        text=text,
        command=command,
        fg=fg,
        bg=bg,
        activeforeground=fg,
        activebackground=BG_SECTION,
        relief="solid",
        bd=1,
        font=f,
        cursor="hand2",
        padx=10,
        pady=4,
        **kw,
    )
    button.bind("<Enter>", lambda event: button.config(bg=BG_SECTION))
    button.bind("<Leave>", lambda event: button.config(bg=bg))
    return button


class MergeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Merger")
        self.root.geometry("700x730")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self._file_set: set[str] = set()
        self._file_list: list[str] = []

        self.folder_var = tk.StringVar()
        self.ext_vars: dict[str, tk.IntVar] = {}
        self.output_var = tk.StringVar(value="output.txt")

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = self.root

        hdr = tk.Frame(root, bg=BG_WHITE, bd=0)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")

        inner_hdr = tk.Frame(hdr, bg=BG_WHITE)
        inner_hdr.pack(fill="x", padx=20, pady=10)

        tk.Label(
            inner_hdr,
            text="File Merger",
            font=("Segoe UI", 16, "bold"),
            bg=BG_WHITE,
            fg=TEXT,
        ).pack(side="left")

        tk.Label(
            inner_hdr,
            text="accumula e unisci sorgenti",
            font=("Segoe UI", 10),
            bg=BG_WHITE,
            fg=TEXT_MUTED,
        ).pack(side="left", padx=12)

        main_area = tk.Frame(root, bg=BG)
        main_area.pack(fill="both", expand=True)

        self._main_canvas = tk.Canvas(
            main_area,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        main_scrollbar = tk.Scrollbar(
            main_area,
            orient="vertical",
            command=self._main_canvas.yview,
        )
        self._main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_scrollbar.pack(side="right", fill="y")
        self._main_canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(self._main_canvas, bg=BG)
        self._main_canvas_window = self._main_canvas.create_window(
            (0, 0),
            window=content,
            anchor="nw",
        )

        content.bind("<Configure>", self._update_main_scrollregion)
        self._main_canvas.bind("<Configure>", self._resize_main_content)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)

        content.configure(padx=18, pady=12)

        self._section(content, "Destinazione")

        row_folder = tk.Frame(content, bg=BG)
        row_folder.pack(fill="x", pady=(0, 4))

        tk.Label(
            row_folder,
            text="Cartella output",
            font=("Segoe UI", 9),
            bg=BG,
            fg=TEXT_MUTED,
            width=14,
            anchor="w",
        ).pack(side="left")

        tk.Entry(
            row_folder,
            textvariable=self.folder_var,
            font=("Segoe UI", 9),
            bg=BG_WHITE,
            fg=TEXT,
            relief="solid",
            bd=1,
        ).pack(side="left", fill="x", expand=True, padx=(4, 6))

        _btn(row_folder, "Sfoglia...", self._choose_folder).pack(side="left")

        row_out = tk.Frame(content, bg=BG)
        row_out.pack(fill="x", pady=(0, 10))

        tk.Label(
            row_out,
            text="Nome output",
            font=("Segoe UI", 9),
            bg=BG,
            fg=TEXT_MUTED,
            width=14,
            anchor="w",
        ).pack(side="left")

        tk.Entry(
            row_out,
            textvariable=self.output_var,
            font=("Segoe UI", 9),
            bg=BG_WHITE,
            fg=TEXT,
            relief="solid",
            bd=1,
            width=28,
        ).pack(side="left", padx=4)

        self._section(content, "File da unire")

        drop_text = (
            "Trascina qui file o cartelle, oppure usa i pulsanti ->"
            if HAS_DND
            else "Usa i pulsanti per aggiungere file o cartelle"
        )

        self._drop_frame = tk.Frame(
            content,
            bg=BG_WHITE,
            bd=1,
            relief="solid",
            highlightbackground=BORDER,
        )
        self._drop_frame.pack(fill="x", pady=(0, 6))

        self._drop_hint = tk.Label(
            self._drop_frame,
            text=drop_text,
            font=("Segoe UI", 9),
            bg=BG_WHITE,
            fg=TEXT_MUTED,
            pady=8,
        )
        self._drop_hint.pack()

        list_outer = tk.Frame(content, bg=BG_WHITE, bd=1, relief="solid")
        list_outer.pack(fill="both", expand=True, pady=(0, 4))

        vsb = tk.Scrollbar(list_outer)
        vsb.pack(side="right", fill="y")

        self._listbox = tk.Listbox(
            list_outer,
            yscrollcommand=vsb.set,
            bg=BG_WHITE,
            fg=TEXT,
            selectbackground="#dbeafe",
            selectforeground=TEXT,
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            height=7,
            activestyle="none",
        )
        self._listbox.pack(fill="both", expand=True, padx=4, pady=4)
        vsb.config(command=self._listbox.yview)

        self._count_label = tk.Label(
            content,
            text="Nessun file in lista",
            font=("Segoe UI", 8),
            bg=BG,
            fg=TEXT_MUTED,
            anchor="w",
        )
        self._count_label.pack(fill="x", pady=(0, 6))

        btn_row = tk.Frame(content, bg=BG)
        btn_row.pack(fill="x", pady=(0, 12))

        _btn(btn_row, "+ Aggiungi file", self._add_files).pack(
            side="left", padx=(0, 6)
        )
        _btn(btn_row, "+ Aggiungi cartella", self._add_folder_files).pack(
            side="left", padx=(0, 6)
        )
        _btn(btn_row, "Rimuovi selezionati", self._remove_selected).pack(
            side="left", padx=(0, 6)
        )

        clear_btn = tk.Button(
            btn_row,
            text="Svuota lista",
            command=self._clear_list,
            fg=BTN_DANGER,
            bg=BTN_BG,
            activeforeground=BTN_DANGER_H,
            activebackground=BG_SECTION,
            relief="solid",
            bd=1,
            font=("Segoe UI", 9),
            cursor="hand2",
            padx=10,
            pady=4,
        )
        clear_btn.pack(side="right")
        clear_btn.bind("<Enter>", lambda event: clear_btn.config(bg="#fef2f2"))
        clear_btn.bind("<Leave>", lambda event: clear_btn.config(bg=BTN_BG))

        self._section(content, "Estensioni rilevate")

        ext_box = tk.Frame(content, bg=BG_WHITE, bd=1, relief="solid")
        ext_box.pack(fill="x", pady=(0, 6))

        self._ext_canvas = tk.Canvas(
            ext_box,
            bg=BG_WHITE,
            highlightthickness=0,
            height=150,
        )
        vsb2 = tk.Scrollbar(
            ext_box,
            orient="vertical",
            command=self._ext_canvas.yview,
        )
        self._ext_canvas.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")
        self._ext_canvas.pack(side="left", fill="both", expand=True)

        self._ext_inner = tk.Frame(self._ext_canvas, bg=BG_WHITE)
        self._ext_canvas_window = self._ext_canvas.create_window(
            (0, 0),
            window=self._ext_inner,
            anchor="nw",
        )

        self._ext_inner.bind(
            "<Configure>",
            lambda event: self._ext_canvas.configure(
                scrollregion=self._ext_canvas.bbox("all")
            ),
        )
        self._ext_canvas.bind(
            "<Configure>",
            lambda event: self._ext_canvas.itemconfig(
                self._ext_canvas_window,
                width=event.width,
            ),
        )
        self._refresh_extension_controls()

        sel_row = tk.Frame(content, bg=BG)
        sel_row.pack(fill="x", pady=(0, 10))
        _btn(sel_row, "Seleziona tutto", lambda: self._set_all_ext(1)).pack(
            side="left", padx=(0, 6)
        )
        _btn(sel_row, "Deseleziona tutto", lambda: self._set_all_ext(0)).pack(
            side="left"
        )

        gen_btn = tk.Button(
            content,
            text="Genera output",
            command=self._generate_output,
            fg=BTN_OK_FG,
            bg=BTN_OK_BG,
            activeforeground=BTN_OK_FG,
            activebackground=ACCENT_HOVER,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=14,
            pady=8,
        )
        gen_btn.pack(fill="x")

        if HAS_DND:
            for widget in (self._drop_frame, self._drop_hint, self._listbox):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)

    def _update_main_scrollregion(self, event=None):
        self._main_canvas.configure(
            scrollregion=self._main_canvas.bbox("all")
        )

    def _resize_main_content(self, event):
        self._main_canvas.itemconfig(
            self._main_canvas_window,
            width=event.width,
        )

    def _pointer_is_over(self, widget):
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        return (
            widget.winfo_rootx() <= x < widget.winfo_rootx() + widget.winfo_width()
            and widget.winfo_rooty() <= y < widget.winfo_rooty() + widget.winfo_height()
        )

    def _on_mousewheel(self, event):
        target = (
            self._ext_canvas
            if self._pointer_is_over(self._ext_canvas)
            else self._main_canvas
        )

        if getattr(event, "num", None) == 4:
            direction = -1
        elif getattr(event, "num", None) == 5:
            direction = 1
        else:
            direction = int(-1 * (event.delta / 120))

        if direction:
            target.yview_scroll(direction, "units")

        return "break"

    def _section(self, parent, title):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", pady=(4, 4))

        tk.Label(
            frame,
            text=title,
            font=("Segoe UI", 9, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(side="left")

        tk.Frame(frame, bg=BORDER, height=1).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0),
            pady=6,
        )

    # ------------------------------------------------------------------
    # Gestione dinamica delle estensioni
    # ------------------------------------------------------------------

    def _extension_from_path(self, path):
        filename = os.path.basename(path).lower()
        _, extension = os.path.splitext(filename)

        if extension:
            return extension[1:]

        return filename

    def _discover_extensions(self, paths):
        discovered = set()

        for path in paths:
            if os.path.isdir(path):
                for root_dir, dirs, files in os.walk(path):
                    dirs[:] = [directory for directory in dirs if not directory.startswith(".")]

                    for filename in files:
                        extension = self._extension_from_path(filename)
                        if extension:
                            discovered.add(extension)

            elif os.path.isfile(path):
                extension = self._extension_from_path(path)
                if extension:
                    discovered.add(extension)

        return discovered

    def _register_extensions(self, extensions):
        changed = False

        for extension in sorted(extensions):
            if extension in self.ext_vars:
                continue

            default_value = (
                1
                if extension not in KNOWN_EXTENSIONS or extension in DEFAULT_ON
                else 0
            )
            self.ext_vars[extension] = tk.IntVar(value=default_value)
            changed = True

        if changed:
            self._refresh_extension_controls()

    def _refresh_extension_controls(self):
        for widget in self._ext_inner.winfo_children():
            widget.destroy()

        if not self.ext_vars:
            tk.Label(
                self._ext_inner,
                text=(
                    "Le estensioni compariranno automaticamente "
                    "quando aggiungi file o cartelle."
                ),
                font=("Segoe UI", 9),
                bg=BG_WHITE,
                fg=TEXT_MUTED,
                anchor="w",
                justify="left",
            ).grid(row=0, column=0, sticky="w", padx=8, pady=10)
            return

        columns = 6
        for index, extension in enumerate(sorted(self.ext_vars)):
            row = index // columns
            column = index % columns

            tk.Checkbutton(
                self._ext_inner,
                text=f".{extension}",
                variable=self.ext_vars[extension],
                bg=BG_WHITE,
                fg=TEXT,
                selectcolor=BG_WHITE,
                activebackground=BG_WHITE,
                font=("Segoe UI", 9),
                cursor="hand2",
            ).grid(row=row, column=column, sticky="w", padx=6, pady=3)

    def _selected_extensions(self):
        return [
            extension
            for extension, variable in self.ext_vars.items()
            if variable.get() == 1
        ]

    def _matches_selected_extension(self, path):
        return self._extension_from_path(path) in self._selected_extensions()

    # ------------------------------------------------------------------
    # Gestione della lista dei file
    # ------------------------------------------------------------------

    def _add_paths(self, paths):
        self._register_extensions(self._discover_extensions(paths))
        added = 0

        for path in paths:
            if os.path.isdir(path):
                for root_dir, dirs, files in os.walk(path):
                    dirs[:] = [directory for directory in dirs if not directory.startswith(".")]

                    for filename in sorted(files):
                        full = os.path.abspath(os.path.join(root_dir, filename))

                        if not self._matches_selected_extension(full):
                            continue

                        if full not in self._file_set:
                            self._file_set.add(full)
                            self._file_list.append(full)
                            added += 1

            elif os.path.isfile(path):
                full = os.path.abspath(path)

                # La versione precedente accettava sempre i singoli file.
                if full not in self._file_set:
                    self._file_set.add(full)
                    self._file_list.append(full)
                    added += 1

        self._refresh_listbox()
        return added

    def _refresh_listbox(self):
        self._listbox.delete(0, "end")

        for filepath in self._file_list:
            self._listbox.insert("end", "  " + filepath)

        count = len(self._file_list)
        if count == 0:
            self._count_label.config(text="Nessun file in lista", fg=TEXT_MUTED)
        else:
            self._count_label.config(text=f"{count} file in lista", fg=TEXT)

    def _clear_list(self):
        self._file_set.clear()
        self._file_list.clear()
        self._refresh_listbox()

    def _remove_selected(self):
        for index in sorted(self._listbox.curselection(), reverse=True):
            self._file_set.discard(self._file_list[index])
            del self._file_list[index]

        self._refresh_listbox()

    # ------------------------------------------------------------------
    # Callback
    # ------------------------------------------------------------------

    def _choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def _add_files(self):
        paths = filedialog.askopenfilenames(title="Seleziona file")

        if paths:
            added = self._add_paths(list(paths))
            if added == 0:
                messagebox.showinfo(
                    "Nessun file aggiunto",
                    "I file selezionati erano gia presenti nella lista.",
                )

    def _add_folder_files(self):
        folder = filedialog.askdirectory(title="Seleziona cartella")

        if folder:
            added = self._add_paths([folder])
            if added == 0:
                messagebox.showinfo(
                    "Nessun file trovato",
                    "Nessun nuovo file corrisponde alle estensioni attive.",
                )
            else:
                messagebox.showinfo("Aggiunto", f"{added} file aggiunti.")

    def _on_drop(self, event):
        try:
            paths = list(self.root.tk.splitlist(event.data))
        except tk.TclError:
            paths = [
                path.strip("{}")
                for path in re.findall(r"\{[^}]+\}|[^\s]+", event.data)
            ]

        if paths:
            added = self._add_paths(paths)
            message = (
                f"OK: {added} file aggiunti"
                if added
                else "Nessun nuovo file compatibile"
            )
            color = TEXT if added else "#e53e3e"
            self._drop_hint.config(text=message, fg=color)
            self.root.after(2500, self._reset_drop_hint)

    def _reset_drop_hint(self):
        self._drop_hint.config(
            text="Trascina qui file o cartelle, oppure usa i pulsanti ->",
            fg=TEXT_MUTED,
        )

    def _set_all_ext(self, value):
        for variable in self.ext_vars.values():
            variable.set(value)

    # ------------------------------------------------------------------
    # Generazione
    # ------------------------------------------------------------------

    def _generate_output(self):
        folder = self.folder_var.get().strip()
        output_name = self.output_var.get().strip() or "output.txt"

        if self._file_list:
            if not folder:
                folder = os.path.dirname(self._file_list[0])
                self.folder_var.set(folder)

            output_path = os.path.join(folder, output_name)

            try:
                merge_file_list(self._file_list, output_path)
                messagebox.showinfo(
                    "Fatto!",
                    f"{len(self._file_list)} file uniti in:\n{output_path}",
                )
            except Exception as error:
                messagebox.showerror("Errore", str(error))

        else:
            if not folder:
                messagebox.showerror(
                    "Errore",
                    "Aggiungi file alla lista oppure seleziona una cartella.",
                )
                return

            self._register_extensions(self._discover_extensions([folder]))
            selected_extensions = self._selected_extensions()

            if not selected_extensions:
                messagebox.showerror(
                    "Errore",
                    "Seleziona almeno un'estensione.",
                )
                return

            try:
                output_path = merge_files(
                    folder,
                    selected_extensions,
                    output_name,
                )
                messagebox.showinfo(
                    "Fatto!",
                    f"File generato:\n{output_path}",
                )
            except Exception as error:
                messagebox.showerror("Errore", str(error))
