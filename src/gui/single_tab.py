import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from analysis.scoring import analyze_single_image
from results.csv_writer import write_single_result
from gui.preview import load_thumbnail

IMAGE_FILETYPES = [
    ("Images", "*.jpg *.jpeg *.png *.bmp *.webp"),
    ("All files", "*.*"),
]

RESULT_STYLE = {
    "tends to have AI-generated visual characteristics": ("AI-generated", "#2563eb"),
    "tends to have real image visual characteristics": ("Real image", "#16a34a"),
    "inconclusive": ("Inconclusive", "#9ca3af"),
}

class SingleImageTab(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=16)
        self.image_path = tk.StringVar()
        self.analysis = None
        self.photo = None
        self._build()

    def _build(self) -> None:
        picker = ttk.Frame(self)
        picker.pack(fill="x")
        ttk.Label(picker, text="Image").pack(side="left")
        entry = ttk.Entry(picker, textvariable=self.image_path, state="readonly")
        entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(picker, text="Browse...", command=self._browse).pack(side="left")

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Analyze", command=self._analyze).pack(side="left")
        self.save_button = ttk.Button(actions, text="Save CSV", command=self._save, state="disabled")
        self.save_button.pack(side="left", padx=8)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        self.preview = ttk.Label(body, text="No image", anchor="center", relief="solid", width=34)
        self.preview.pack(side="left", anchor="n", padx=(0, 16))

        results = ttk.Frame(body)
        results.pack(side="left", fill="both", expand=True)

        self.verdict = ttk.Label(results, text="—", font=("Segoe UI", 16, "bold"))
        self.verdict.pack(anchor="w")
        self.confidence_label = ttk.Label(results, text="")
        self.confidence_label.pack(anchor="w", pady=(0, 8))

        self.scores = ttk.Label(results, text="", justify="left", font=("Consolas", 10))
        self.scores.pack(anchor="w")

        ttk.Label(results, text="Visual string (64 symbols):").pack(anchor="w", pady=(12, 2))
        self.visual = tk.Text(results, height=4, wrap="word", font=("Consolas", 10))
        self.visual.configure(state="disabled")
        self.visual.pack(fill="x")

    def _browse(self) -> None:
        path = filedialog.askopenfilename(title="Select image", filetypes=IMAGE_FILETYPES)
        if path:
            self.image_path.set(path)
            self._show_preview(path)

    def _show_preview(self, path: str) -> None:
        data = load_thumbnail(path)
        if data is None:
            self.photo = None
            self.preview.configure(image="", text="Cannot preview")
            return
        self.photo = tk.PhotoImage(data=data)
        self.preview.configure(image=self.photo, text="")

    def _analyze(self) -> None:
        path = self.image_path.get()
        if not path:
            messagebox.showwarning("No image", "Please choose an image first.")
            return
        try:
            self.analysis = analyze_single_image(path)
        except (FileNotFoundError, ValueError) as error:
            messagebox.showerror("Error", str(error))
            return
        self._render(self.analysis)
        self.save_button.configure(state="normal")

    def _render(self, analysis: dict) -> None:
        label, color = RESULT_STYLE.get(analysis["result"], (analysis["result"], "#111827"))
        self.verdict.configure(text=label, foreground=color)
        self.confidence_label.configure(text=f"Confidence: {analysis['confidence']:.3f}")
        rows = [
            ("AI score", analysis["ai_score"]),
            ("Real score", analysis["real_score"]),
            ("AI exact match", analysis["ai_exact_score"]),
            ("AI regex match", analysis["ai_regex_score"]),
            ("Real exact match", analysis["real_exact_score"]),
            ("Real regex match", analysis["real_regex_score"]),
        ]
        text = "\n".join(f"{label:<18}: {value}" for label, value in rows)
        self.scores.configure(text=text)
        self.visual.configure(state="normal")
        self.visual.delete("1.0", "end")
        self.visual.insert("1.0", analysis["visual_string"])
        self.visual.configure(state="disabled")

    def _save(self) -> None:
        if self.analysis is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            initialdir="output",
            initialfile="single_result.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        write_single_result(path, self.analysis)
        messagebox.showinfo("Saved", f"Result saved to:\n{path}")