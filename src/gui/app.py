import tkinter as tk
from tkinter import ttk
from gui.compare_tab import CompareTab
from gui.single_tab import SingleImageTab

def _apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    for preferred in ("vista", "clam"):
        if preferred in style.theme_names():
            style.theme_use(preferred)
            break

def main() -> None:
    root = tk.Tk()
    root.title("Visual Pattern Image Analyzer")
    root.geometry("860x620")
    root.minsize(720, 560)
    _apply_theme(root)

    header = ttk.Label(
        root,
        text="AI vs Real Image Analysis - Visual Pattern Strings",
        font=("Segoe UI", 14, "bold"),
        padding=(12, 10),
    )
    header.pack(anchor="w")
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    notebook.add(SingleImageTab(notebook), text="Single Image")
    notebook.add(CompareTab(notebook), text="Compare Two Images")
    root.mainloop()

if __name__ == "__main__":
    main()