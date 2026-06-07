# gui.py
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont
from business_logic import merge_files, merge_file_list

# ---------------------------------------------------------------------------
# Extension catalogue
# ---------------------------------------------------------------------------
EXTENSION_GROUPS = {
    "Web / Frontend": [
        "html", "htm", "css", "scss", "sass", "less",
        "js", "mjs", "cjs", "jsx",
    ],
    "TypeScript": [
        "ts", "tsx", "d.ts",
    ],
    "Svelte / SvelteKit": [
        "svelte",
    ],
    "Rust / Tauri": [
        "rs", "toml",
    ],
    "Python": [
        "py", "pyw", "pyi",
    ],
    "C / C++ / C#": [
        "c", "h", "cpp", "cc", "cxx", "hpp", "hxx", "cs",
    ],
    "Java / Kotlin / Scala": [
        "java", "kt", "kts", "scala",
    ],
    "Go / Swift / Dart": [
        "go", "swift", "dart",
    ],
    "Ruby / PHP / Lua": [
        "rb", "php", "lua",
    ],
    "Shell / Config": [
        "sh", "bash", "zsh", "fish", "ps1",
        "env", "cfg", "ini", "conf",
    ],
    "Data / Markup": [
        "json", "json5", "jsonc", "yaml", "yml",
        "xml", "toml", "csv", "sql",
    ],
    "Docs / Text": [
        "md", "mdx", "txt", "rst", "adoc",
    ],
    "Build / Infra": [
        "dockerfile", "makefile", "ninja", "cmake",
        "gradle", "tf", "hcl",
    ],
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
# Palette – light, clean, professional
# ---------------------------------------------------------------------------
BG          = "#f5f5f5"
BG_WHITE    = "#ffffff"
BG_SECTION  = "#efefef"
BORDER      = "#d0d0d0"
TEXT        = "#222222"
TEXT_MUTED  = "#888888"
ACCENT      = "#2563eb"        # blue – used sparingly
ACCENT_HOVER= "#1d4ed8"
BTN_BG      = "#ffffff"
BTN_BORDER  = "#c0c0c0"
BTN_DANGER  = "#dc2626"
BTN_DANGER_H= "#b91c1c"
BTN_OK_BG   = "#2563eb"
BTN_OK_FG   = "#ffffff"
GROUP_FG    = "#555555"

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False


def _btn(parent, text, command, fg=TEXT, bg=BTN_BG, bold=False, **kw):
    """Helper: flat-ish button that highlights on hover."""
    f = ("Segoe UI", 9, "bold") if bold else ("Segoe UI", 9)
    b = tk.Button(
        parent, text=text, command=command,
        fg=fg, bg=bg,
        activeforeground=fg, activebackground=BG_SECTION,
        relief="solid", bd=1,
        font=f, cursor="hand2",
        padx=10, pady=4,
        **kw,
    )
    b.bind("<Enter>", lambda e: b.config(bg=BG_SECTION))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


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

        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=BG_WHITE, bd=0)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=BG_WHITE)
        inner_hdr.pack(fill="x", padx=20, pady=10)
        tk.Label(
            inner_hdr, text="File Merger",
            font=("Segoe UI", 16, "bold"),
            bg=BG_WHITE, fg=TEXT,
        ).pack(side="left")
        tk.Label(
            inner_hdr, text="accumula e unisci sorgenti",
            font=("Segoe UI", 10),
            bg=BG_WHITE, fg=TEXT_MUTED,
        ).pack(side="left", padx=12)

        # ── Main content area ─────────────────────────────────────────
        content = tk.Frame(root, bg=BG)
        content.pack(fill="both", expand=True, padx=18, pady=12)

        # ── Output folder + filename (two rows) ───────────────────────
        self._section(content, "Destinazione")

        row_folder = tk.Frame(content, bg=BG)
        row_folder.pack(fill="x", pady=(0, 4))
        tk.Label(row_folder, text="Cartella output",
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_MUTED,
                 width=14, anchor="w").pack(side="left")
        tk.Entry(
            row_folder, textvariable=self.folder_var,
            font=("Segoe UI", 9), bg=BG_WHITE,
            fg=TEXT, relief="solid", bd=1,
        ).pack(side="left", fill="x", expand=True, padx=(4, 6))
        _btn(row_folder, "Sfoglia…", self._choose_folder).pack(side="left")

        row_out = tk.Frame(content, bg=BG)
        row_out.pack(fill="x", pady=(0, 10))
        tk.Label(row_out, text="Nome output",
                 font=("Segoe UI", 9), bg=BG, fg=TEXT_MUTED,
                 width=14, anchor="w").pack(side="left")
        tk.Entry(
            row_out, textvariable=self.output_var,
            font=("Segoe UI", 9), bg=BG_WHITE,
            fg=TEXT, relief="solid", bd=1, width=28,
        ).pack(side="left", padx=4)

        # ── Drop zone ─────────────────────────────────────────────────
        self._section(content, "File da unire")

        drop_text = (
            "Trascina qui file o cartelle, oppure usa i pulsanti →"
            if HAS_DND else
            "Usa i pulsanti per aggiungere file o cartelle"
        )
        self._drop_frame = tk.Frame(
            content, bg=BG_WHITE,
            bd=1, relief="solid",
            highlightbackground=BORDER,
        )
        self._drop_frame.pack(fill="x", pady=(0, 6))

        self._drop_hint = tk.Label(
            self._drop_frame,
            text=drop_text,
            font=("Segoe UI", 9), bg=BG_WHITE, fg=TEXT_MUTED,
            pady=8,
        )
        self._drop_hint.pack()

        # Listbox
        list_outer = tk.Frame(content, bg=BG_WHITE, bd=1, relief="solid")
        list_outer.pack(fill="both", expand=True, pady=(0, 4))

        vsb = tk.Scrollbar(list_outer)
        vsb.pack(side="right", fill="y")
        self._listbox = tk.Listbox(
            list_outer,
            yscrollcommand=vsb.set,
            bg=BG_WHITE, fg=TEXT,
            selectbackground="#dbeafe",
            selectforeground=TEXT,
            font=("Segoe UI", 9),
            relief="flat", bd=0,
            height=7,
            activestyle="none",
        )
        self._listbox.pack(fill="both", expand=True, padx=4, pady=4)
        vsb.config(command=self._listbox.yview)

        self._count_label = tk.Label(
            content, text="Nessun file in lista",
            font=("Segoe UI", 8), bg=BG, fg=TEXT_MUTED,
            anchor="w",
        )
        self._count_label.pack(fill="x", pady=(0, 6))

        # ── Action buttons ────────────────────────────────────────────
        btn_row = tk.Frame(content, bg=BG)
        btn_row.pack(fill="x", pady=(0, 12))

        _btn(btn_row, "+ Aggiungi file",     self._add_files).pack(side="left", padx=(0, 6))
        _btn(btn_row, "+ Aggiungi cartella", self._add_folder_files).pack(side="left", padx=(0, 6))
        _btn(btn_row, "Rimuovi selezionati", self._remove_selected).pack(side="left", padx=(0, 6))

        # Svuota lista – rosso, a destra
        clear_btn = tk.Button(
            btn_row, text="Svuota lista",
            command=self._clear_list,
            fg=BTN_DANGER, bg=BTN_BG,
            activeforeground=BTN_DANGER_H, activebackground=BG_SECTION,
            relief="solid", bd=1,
            font=("Segoe UI", 9), cursor="hand2",
            padx=10, pady=4,
        )
        clear_btn.pack(side="right")
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(bg="#fef2f2"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(bg=BTN_BG))

        # ── Extensions ────────────────────────────────────────────────
        self._section(content, "Estensioni")

        ext_box = tk.Frame(
            content, bg=BG_WHITE, bd=1, relief="solid",
        )
        ext_box.pack(fill="x", pady=(0, 6))

        # Scrollable canvas
        canvas = tk.Canvas(ext_box, bg=BG_WHITE, highlightthickness=0, height=150)
        vsb2 = tk.Scrollbar(ext_box, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG_WHITE)
        cw = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        COL = 6
        row_i = 0
        col_i = 0
        for group_name, exts in EXTENSION_GROUPS.items():
            tk.Label(
                inner, text=group_name,
                font=("Segoe UI", 8, "bold"),
                bg=BG_WHITE, fg=GROUP_FG, anchor="w",
            ).grid(row=row_i, column=0, columnspan=COL,
                   sticky="w", padx=8, pady=(8, 2))
            row_i += 1
            col_i = 0
            for ext in exts:
                var = tk.IntVar(value=1 if ext in DEFAULT_ON else 0)
                self.ext_vars[ext] = var
                cb = tk.Checkbutton(
                    inner, text=f".{ext}", variable=var,
                    bg=BG_WHITE, fg=TEXT,
                    selectcolor=BG_WHITE,
                    activebackground=BG_WHITE,
                    font=("Segoe UI", 9),
                    cursor="hand2",
                )
                cb.grid(row=row_i, column=col_i, sticky="w", padx=6, pady=1)
                col_i += 1
                if col_i >= COL:
                    col_i = 0
                    row_i += 1
            if col_i != 0:
                row_i += 1
                col_i = 0

        # Select all / deselect all
        sel_row = tk.Frame(content, bg=BG)
        sel_row.pack(fill="x", pady=(0, 10))
        _btn(sel_row, "Seleziona tutto",   lambda: self._set_all_ext(1)).pack(side="left", padx=(0, 6))
        _btn(sel_row, "Deseleziona tutto", lambda: self._set_all_ext(0)).pack(side="left")

        # ── Generate button ────────────────────────────────────────────
        gen_btn = tk.Button(
            content, text="Genera output",
            command=self._generate_output,
            bg=BTN_OK_BG, fg=BTN_OK_FG,
            activebackground=ACCENT_HOVER, activeforeground=BTN_OK_FG,
            relief="flat", bd=0,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2", pady=10,
        )
        gen_btn.pack(fill="x", pady=(0, 6))
        gen_btn.bind("<Enter>", lambda e: gen_btn.config(bg=ACCENT_HOVER))
        gen_btn.bind("<Leave>", lambda e: gen_btn.config(bg=BTN_OK_BG))

        # ── DnD ───────────────────────────────────────────────────────
        if HAS_DND:
            for w in (self._drop_frame, self._drop_hint, self._listbox):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drop)

    # ------------------------------------------------------------------

    def _section(self, parent, title):
        """Thin labelled section divider."""
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(4, 4))
        tk.Label(f, text=title,
                 font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0), pady=6)

    # ------------------------------------------------------------------
    # File list management
    # ------------------------------------------------------------------

    def _selected_extensions(self):
        return [ext for ext, var in self.ext_vars.items() if var.get() == 1]

    def _add_paths(self, paths):
        selected_exts = self._selected_extensions()
        added = 0
        for path in paths:
            if os.path.isdir(path):
                for root_dir, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for f in sorted(files):
                        if any(f.lower().endswith("." + e) for e in selected_exts):
                            full = os.path.abspath(os.path.join(root_dir, f))
                            if full not in self._file_set:
                                self._file_set.add(full)
                                self._file_list.append(full)
                                added += 1
            elif os.path.isfile(path):
                full = os.path.abspath(path)
                if full not in self._file_set:
                    self._file_set.add(full)
                    self._file_list.append(full)
                    added += 1
        self._refresh_listbox()
        return added

    def _refresh_listbox(self):
        self._listbox.delete(0, "end")
        for fp in self._file_list:
            self._listbox.insert("end", "  " + fp)
        n = len(self._file_list)
        if n == 0:
            self._count_label.config(text="Nessun file in lista", fg=TEXT_MUTED)
        else:
            self._count_label.config(text=f"{n} file in lista", fg=TEXT)

    def _clear_list(self):
        self._file_set.clear()
        self._file_list.clear()
        self._refresh_listbox()

    def _remove_selected(self):
        for i in sorted(self._listbox.curselection(), reverse=True):
            self._file_set.discard(self._file_list[i])
            del self._file_list[i]
        self._refresh_listbox()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def _add_files(self):
        if not self._selected_extensions():
            messagebox.showerror("Errore", "Seleziona almeno un'estensione.")
            return
        paths = filedialog.askopenfilenames(title="Seleziona file")
        if paths:
            added = self._add_paths(list(paths))
            if added == 0:
                messagebox.showinfo("Nessun file aggiunto",
                    "I file selezionati non corrispondono alle estensioni attive\n"
                    "o erano già in lista.")

    def _add_folder_files(self):
        if not self._selected_extensions():
            messagebox.showerror("Errore", "Seleziona almeno un'estensione.")
            return
        folder = filedialog.askdirectory(title="Seleziona cartella")
        if folder:
            added = self._add_paths([folder])
            if added == 0:
                messagebox.showinfo("Nessun file trovato",
                    "Nessun file con le estensioni selezionate.")
            else:
                messagebox.showinfo("Aggiunto", f"{added} file aggiunti.")

    def _on_drop(self, event):
        paths = [p.strip("{}") for p in
                 re.findall(r'\{[^}]+\}|[^\s]+', event.data)]
        if paths:
            added = self._add_paths(paths)
            msg = f"✓ {added} file aggiunti" if added else "Nessun file compatibile"
            fg  = TEXT if added else "#e53e3e"
            self._drop_hint.config(text=msg, fg=fg)
            self.root.after(2500, self._reset_drop_hint)

    def _reset_drop_hint(self):
        self._drop_hint.config(
            text="Trascina qui file o cartelle, oppure usa i pulsanti →",
            fg=TEXT_MUTED,
        )

    def _set_all_ext(self, value):
        for var in self.ext_vars.values():
            var.set(value)

    # ------------------------------------------------------------------
    # Generate
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
            except Exception as e:
                messagebox.showerror("Errore", str(e))
        else:
            if not folder:
                messagebox.showerror("Errore",
                    "Aggiungi file alla lista oppure seleziona una cartella.")
                return
            selected_exts = self._selected_extensions()
            if not selected_exts:
                messagebox.showerror("Errore", "Seleziona almeno un'estensione.")
                return
            try:
                output_path = merge_files(folder, selected_exts, output_name)
                messagebox.showinfo("Fatto!", f"File generato:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Errore", str(e))
