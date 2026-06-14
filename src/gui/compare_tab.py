import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from analysis.scoring import compare_two_images
from results.csv_writer import write_compare_result
from gui.preview import load_thumbnail
from gui.single_tab import IMAGE_FILETYPES, RESULT_STYLE

class CompareTab(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=16)
        self.ai_path = tk.StringVar()
        self.real_path = tk.StringVar()
        self.comparison = None
        self.ai_photo = None
        self.real_photo = None
        self._build()

    def _build(self) -> None:
        pickers = ttk.Frame(self)
        pickers.pack(fill="x")
        pickers.columnconfigure(0, weight=1)
        pickers.columnconfigure(1, weight=1)
        self.ai_preview = self._picker(pickers, "AI image", self.ai_path, 0, self._show_ai)
        self.real_preview = self._picker(pickers, "Real image", self.real_path, 1, self._show_real)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Compare", command=self._compare).pack(side="left")
        self.save_button = ttk.Button(actions, text="Save CSV", command=self._save, state="disabled")
        self.save_button.pack(side="left", padx=8)

        details = ttk.Frame(self)
        details.pack(fill="both", expand=True)
        details.columnconfigure(0, weight=1)
        details.columnconfigure(1, weight=1)
        self.ai_detail = self._detail_panel(details, "AI image", 0)
        self.real_detail = self._detail_panel(details, "Real image", 1)

    def _picker(self, parent: tk.Misc, title: str, variable: tk.StringVar, column: int, on_select) -> ttk.Label:
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        left = 0 if column == 0 else 8
        right = 8 if column == 0 else 0
        frame.grid(row=0, column=column, sticky="nsew", padx=(left, right))
        preview = ttk.Label(frame, text="No image", anchor="center", relief="solid", width=22)
        preview.pack(ipady=24)
        entry = ttk.Entry(frame, textvariable=variable, state="readonly")
        entry.pack(fill="x", pady=(8, 4))
        ttk.Button(frame, text="Browse...", command=lambda: self._browse(variable, on_select)).pack()
        return preview

    def _detail_panel(self, parent: tk.Misc, title: str, column: int) -> dict:
        left = 0 if column == 0 else 8
        right = 8 if column == 0 else 0
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky="nsew", padx=(left, right))
        header = ttk.Label(frame, text=title, font=("Segoe UI", 10))
        header.pack(anchor="w")
        verdict = ttk.Label(frame, text="-", font=("Segoe UI", 13, "bold"))
        verdict.pack(anchor="w")
        confidence = ttk.Label(frame, text="")
        confidence.pack(anchor="w", pady=(0, 6))
        scores = ttk.Label(frame, text="", justify="left", font=("Consolas", 10))
        scores.pack(anchor="w")
        ttk.Label(frame, text="Visual string (64 symbols):").pack(anchor="w", pady=(10, 2))
        visual = tk.Text(frame, height=4, wrap="word", font=("Consolas", 9))
        visual.configure(state="disabled")
        visual.pack(fill="x")
        return {"verdict": verdict, "confidence": confidence, "scores": scores, "visual": visual}

    def _browse(self, variable: tk.StringVar, on_select) -> None:
        path = filedialog.askopenfilename(title="Select image", filetypes=IMAGE_FILETYPES)
        if path:
            variable.set(path)
            on_select(path)

    def _show_ai(self, path: str) -> None:
        self.ai_photo = self._set_preview(path, self.ai_preview)

    def _show_real(self, path: str) -> None:
        self.real_photo = self._set_preview(path, self.real_preview)

    def _set_preview(self, path: str, label: ttk.Label):
        data = load_thumbnail(path, 170)
        if data is None:
            label.configure(image="", text="Cannot preview")
            return None
        photo = tk.PhotoImage(data=data)
        label.configure(image=photo, text="")
        return photo

    def _compare(self) -> None:
        ai = self.ai_path.get()
        real = self.real_path.get()
        if not ai or not real:
            messagebox.showwarning("Missing image", "Please choose both an AI image and a real image.")
            return
        try:
            self.comparison = compare_two_images(ai, real)
        except (FileNotFoundError, ValueError) as error:
            messagebox.showerror("Error", str(error))
            return
        self._fill_panel(self.ai_detail, self.comparison["ai_analysis"])
        self._fill_panel(self.real_detail, self.comparison["real_analysis"])
        self.save_button.configure(state="normal")

    def _fill_panel(self, panel: dict, analysis: dict) -> None:
        label, color = RESULT_STYLE.get(analysis["result"], (analysis["result"], "#111827"))
        panel["verdict"].configure(text=label, foreground=color)
        panel["confidence"].configure(text=f"Confidence: {analysis['confidence']:.3f}")
        rows = [
            ("AI score", analysis["ai_score"]),
            ("Real score", analysis["real_score"]),
            ("AI exact match", analysis["ai_exact_score"]),
            ("AI regex match", analysis["ai_regex_score"]),
            ("Real exact match", analysis["real_exact_score"]),
            ("Real regex match", analysis["real_regex_score"]),
        ]
        text = "\n".join(f"{name:<18}: {value}" for name, value in rows)
        panel["scores"].configure(text=text)
        panel["visual"].configure(state="normal")
        panel["visual"].delete("1.0", "end")
        panel["visual"].insert("1.0", analysis["visual_string"])
        panel["visual"].configure(state="disabled")

    def _save(self) -> None:
        if self.comparison is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            initialdir="output",
            initialfile="compare_result.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        write_compare_result(path, self.comparison)
        messagebox.showinfo("Saved", f"Result saved to:\n{path}")