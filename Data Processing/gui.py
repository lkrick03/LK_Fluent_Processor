"""
CFD Data Processing - Tkinter GUI
Graphical front-end for main.py. Run this file instead of main.py
to configure and launch the workflow from a GUI.

Usage:
    python gui.py

Author: Auto-generated
Date: February 2026
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import sys
import io
import os
import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


# ── Stdout / Stderr redirect ────────────────────────────────────────────────

class QueueWriter(io.TextIOBase):
    """Redirect writes to a thread-safe queue for the GUI to consume."""

    def __init__(self, q: queue.Queue):
        super().__init__()
        self._q = q

    def write(self, text: str):
        if text:
            self._q.put(text)
        return len(text) if text else 0

    def flush(self):
        pass


# ── Main Application ────────────────────────────────────────────────────────

class CFDApp(tk.Tk):
    COMPARISON_MODES = ["default", "turbulence", "grid", "mesh", "version", "expanded"]
    EXTRACTION_METHODS = ["case_file", "folder"]
    NAMING_SCHEMAS = ["5-part", "4-part"]

    def __init__(self):
        super().__init__()
        self.title("CFD Data Processing")
        self.minsize(780, 820)
        self.resizable(True, True)

        # Threading
        self._log_queue: queue.Queue = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._running = False

        self._build_ui()
        self._load_defaults()
        self._poll_log_queue()

    # ─── UI Construction ─────────────────────────────────────────────────

    def _build_ui(self):
        # Use a canvas + scrollbar so the whole form scrolls if the window
        # is too small.
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0)
        vscroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self._form = ttk.Frame(canvas)

        self._form.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._form, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        # Enable mouse-wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        pad = {"padx": 8, "pady": 4}
        row = 0

        # ── Section: Data Sources ────────────────────────────────────────
        lf = ttk.LabelFrame(self._form, text="Data Sources (priority list)")
        lf.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        row += 1

        self.src_listbox = tk.Listbox(lf, height=5, selectmode="extended", width=90)
        self.src_listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        src_scroll = ttk.Scrollbar(lf, orient="vertical", command=self.src_listbox.yview)
        self.src_listbox.configure(yscrollcommand=src_scroll.set)
        src_scroll.pack(side="left", fill="y")

        btn_frame = ttk.Frame(lf)
        btn_frame.pack(side="left", padx=4)
        ttk.Button(btn_frame, text="+ Add", command=self._add_source).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="− Remove", command=self._remove_source).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Clear All", command=self._clear_sources).pack(fill="x", pady=2)

        # ── Section: Output Directory ────────────────────────────────────
        lf2 = ttk.LabelFrame(self._form, text="Output Directory")
        lf2.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        row += 1

        self.output_var = tk.StringVar()
        ttk.Entry(lf2, textvariable=self.output_var, width=80).pack(side="left", padx=4, pady=4, fill="x", expand=True)
        ttk.Button(lf2, text="Browse…", command=self._browse_output).pack(side="left", padx=4)

        # ── Section: Processing Options ──────────────────────────────────
        lf3 = ttk.LabelFrame(self._form, text="Processing Options")
        lf3.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        row += 1

        opts = ttk.Frame(lf3)
        opts.pack(fill="x", padx=4, pady=4)

        ttk.Label(opts, text="Comparison Mode:").grid(row=0, column=0, sticky="w", padx=4)
        self.mode_var = tk.StringVar()
        ttk.Combobox(opts, textvariable=self.mode_var, values=self.COMPARISON_MODES,
                     state="readonly", width=14).grid(row=0, column=1, padx=4)

        ttk.Label(opts, text="Config Extraction:").grid(row=0, column=2, sticky="w", padx=4)
        self.extraction_var = tk.StringVar()
        ttk.Combobox(opts, textvariable=self.extraction_var, values=self.EXTRACTION_METHODS,
                     state="readonly", width=14).grid(row=0, column=3, padx=4)

        ttk.Label(opts, text="Naming Schema:").grid(row=1, column=0, sticky="w", padx=4, pady=(4, 0))
        self.schema_var = tk.StringVar()
        ttk.Combobox(opts, textvariable=self.schema_var, values=self.NAMING_SCHEMAS,
                     state="readonly", width=14).grid(row=1, column=1, padx=4, pady=(4, 0))

        ttk.Label(opts, text="Iterations for Stats:").grid(row=1, column=2, sticky="w", padx=4, pady=(4, 0))
        self.iter_var = tk.IntVar()
        ttk.Spinbox(opts, textvariable=self.iter_var, from_=1, to=100000,
                    width=10).grid(row=1, column=3, padx=4, pady=(4, 0))

        # ── Section: AoA Filter ──────────────────────────────────────────
        lf4 = ttk.LabelFrame(self._form, text="AoA Filter (comma-separated, blank = all)")
        lf4.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        row += 1

        self.aoa_var = tk.StringVar()
        ttk.Entry(lf4, textvariable=self.aoa_var, width=60).pack(padx=4, pady=4, fill="x")

        # ── Section: Convergence Analysis ────────────────────────────────
        lf5 = ttk.LabelFrame(self._form, text="Convergence Analysis")
        lf5.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        row += 1

        conv = ttk.Frame(lf5)
        conv.pack(fill="x", padx=4, pady=4)

        self.conv_var = tk.BooleanVar()
        ttk.Checkbutton(conv, text="Enable Convergence Analysis",
                        variable=self.conv_var).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(conv, text="Max Trim (%):").grid(row=1, column=0, sticky="w", padx=4)
        self.trim_var = tk.DoubleVar()
        self.trim_scale = ttk.Scale(conv, variable=self.trim_var, from_=10, to=100,
                                    orient="horizontal", length=200,
                                    command=self._update_trim_label)
        self.trim_scale.grid(row=1, column=1, padx=4)
        self.trim_label = ttk.Label(conv, text="90%")
        self.trim_label.grid(row=1, column=2, padx=4)

        ttk.Label(conv, text="Num Tests:").grid(row=2, column=0, sticky="w", padx=4)
        self.tests_var = tk.IntVar()
        ttk.Spinbox(conv, textvariable=self.tests_var, from_=5, to=200,
                    width=10).grid(row=2, column=1, sticky="w", padx=4)

        ttk.Label(conv, text="Graph Max COV (%):").grid(row=3, column=0, sticky="w", padx=4)
        self.cov_var = tk.IntVar()
        ttk.Spinbox(conv, textvariable=self.cov_var, from_=1, to=100,
                    width=10).grid(row=3, column=1, sticky="w", padx=4)

        # ── Section: Physics Parameters ──────────────────────────────────
        lf6 = ttk.LabelFrame(self._form, text="Physics Parameters")
        lf6.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        row += 1

        phys = ttk.Frame(lf6)
        phys.pack(fill="x", padx=4, pady=4)

        self.span_var = tk.StringVar()
        self.chord_var = tk.StringVar()
        self.density_var = tk.StringVar()
        self.velocity_var = tk.StringVar()
        self.viscosity_var = tk.StringVar()

        # (label, variable, grid_row, grid_col) — reference labels stored for later
        self._phys_default_labels: dict[str, ttk.Label] = {}
        params = [
            ("Span (m):", self.span_var, 0, 0, "span"),
            ("Chord (m):", self.chord_var, 0, 3, "chord"),
            ("Air Density (kg/m³):", self.density_var, 1, 0, "density"),
            ("Velocity (m/s):", self.velocity_var, 1, 3, "velocity"),
            ("Viscosity (kg/(m·s)):", self.viscosity_var, 2, 0, "viscosity"),
        ]
        for label, var, r, c, key in params:
            ttk.Label(phys, text=label).grid(row=r, column=c, sticky="w", padx=4, pady=2)
            ttk.Entry(phys, textvariable=var, width=14).grid(row=r, column=c + 1, padx=4, pady=2)
            ref_lbl = ttk.Label(phys, text="", foreground="gray")
            ref_lbl.grid(row=r, column=c + 2, sticky="w", padx=(0, 12), pady=2)
            self._phys_default_labels[key] = ref_lbl
            # Auto-update derived values whenever a physics field changes
            var.trace_add("write", lambda *_: self._update_derived_values())

        # Derived values row (read-only, auto-computed)
        sep = ttk.Separator(phys, orient="horizontal")
        sep.grid(row=3, column=0, columnspan=7, sticky="ew", pady=(6, 2))
        self._derived_label = ttk.Label(phys, text="", foreground="#555555")
        self._derived_label.grid(row=4, column=0, columnspan=7, sticky="w", padx=4, pady=2)

        # ── Section: XY Data Source ──────────────────────────────────────
        lf7 = ttk.LabelFrame(self._form, text="XY Data Source Directory (for Cp / Y+ plots, default mode only)")
        lf7.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        row += 1

        self.xy_var = tk.StringVar()
        ttk.Entry(lf7, textvariable=self.xy_var, width=80).pack(side="left", padx=4, pady=4, fill="x", expand=True)
        ttk.Button(lf7, text="Browse…", command=self._browse_xy).pack(side="left", padx=4)

        # ── Run / Stop Buttons ───────────────────────────────────────────
        btn_bar = ttk.Frame(self._form)
        btn_bar.grid(row=row, column=0, columnspan=3, pady=6)
        row += 1

        self.run_btn = ttk.Button(btn_bar, text="▶  Run Processing", command=self._on_run)
        self.run_btn.pack(side="left", padx=8)

        self.stop_btn = ttk.Button(btn_bar, text="■  Stop", command=self._on_stop, state="disabled")
        self.stop_btn.pack(side="left", padx=8)

        # ── Console Output ───────────────────────────────────────────────
        lf8 = ttk.LabelFrame(self._form, text="Console Output")
        lf8.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        row += 1

        self._form.rowconfigure(row - 1, weight=1)
        self._form.columnconfigure(0, weight=1)

        self.console = tk.Text(lf8, height=16, wrap="word", state="disabled",
                               bg="#1e1e1e", fg="#d4d4d4",
                               font=("Consolas", 9), insertbackground="#d4d4d4")
        console_scroll = ttk.Scrollbar(lf8, orient="vertical", command=self.console.yview)
        self.console.configure(yscrollcommand=console_scroll.set)
        self.console.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        console_scroll.pack(side="right", fill="y", pady=4)

        ttk.Button(self._form, text="Clear Console", command=self._clear_console).grid(
            row=row, column=0, columnspan=3, pady=(0, 6))
        row += 1

        # ── Section: Results Viewer ───────────────────────────────────────
        lf9 = ttk.LabelFrame(self._form, text="Results Viewer")
        lf9.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        row += 1

        self._form.rowconfigure(row - 1, weight=1)

        results_pane = ttk.PanedWindow(lf9, orient="horizontal")
        results_pane.pack(fill="both", expand=True, padx=4, pady=4)

        # Left: file tree
        tree_frame = ttk.Frame(results_pane)
        results_pane.add(tree_frame, weight=1)

        self.results_tree = ttk.Treeview(tree_frame, height=10, selectmode="browse",
                                          columns=("path",), displaycolumns=())
        self.results_tree.heading("#0", text="Generated Files", anchor="w")
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical",
                                     command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scroll.set)
        self.results_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_select)
        self.results_tree.bind("<Double-1>", lambda e: self._open_selected_file())

        # Right: image preview with slideshow navigation
        preview_frame = ttk.Frame(results_pane)
        results_pane.add(preview_frame, weight=2)

        # Slideshow nav bar
        nav_bar = ttk.Frame(preview_frame)
        nav_bar.pack(fill="x", pady=(0, 2))
        self._prev_btn = ttk.Button(nav_bar, text="◀ Prev", command=self._slide_prev, state="disabled")
        self._prev_btn.pack(side="left", padx=4)
        self._slide_info = ttk.Label(nav_bar, text="", anchor="center")
        self._slide_info.pack(side="left", fill="x", expand=True)
        self._next_btn = ttk.Button(nav_bar, text="Next ▶", command=self._slide_next, state="disabled")
        self._next_btn.pack(side="right", padx=4)

        self._preview_label = ttk.Label(preview_frame, text="Select a graph to preview",
                                        anchor="center")
        self._preview_label.pack(fill="both", expand=True)
        self._preview_photo = None  # keep reference to prevent GC

        # Slideshow state
        self._slideshow: list[Path] = []
        self._slide_idx: int = 0

        # Buttons below results
        results_btns = ttk.Frame(lf9)
        results_btns.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(results_btns, text="Open Selected",
                   command=self._open_selected_file).pack(side="left", padx=4)
        ttk.Button(results_btns, text="Open Output Folder",
                   command=self._open_output_folder).pack(side="left", padx=4)
        ttk.Button(results_btns, text="↻ Refresh",
                   command=self._populate_results).pack(side="left", padx=4)

    # ─── Load defaults from the current main.py module-level values ──────

    def _load_defaults(self):
        """Populate the GUI fields with the current defaults from main.py."""
        try:
            import main as _main_mod
            # Data sources
            for src in _main_mod.DATA_SOURCES:
                self.src_listbox.insert("end", str(src))

            self.output_var.set(str(_main_mod.OUTPUT_DIR))
            self.mode_var.set(_main_mod.COMPARISON_MODE)
            self.extraction_var.set(_main_mod.CONFIG_EXTRACTION_METHOD)
            self.iter_var.set(_main_mod.NUM_ITERATIONS)

            # AoA filter
            if _main_mod.AOA_FILTER:
                self.aoa_var.set(", ".join(str(a) for a in _main_mod.AOA_FILTER))

            # Convergence
            self.conv_var.set(_main_mod.RUN_CONVERGENCE_ANALYSIS)
            self.trim_var.set(_main_mod.CONVERGENCE_MAX_TRIM * 100)
            self._update_trim_label(None)
            self.tests_var.set(_main_mod.CONVERGENCE_NUM_TESTS)
            self.cov_var.set(_main_mod.GRAPH_MAX_COV)

            # Physics
            self.span_var.set(str(_main_mod.SPAN))
            self.chord_var.set(str(_main_mod.CHORD))
            self.density_var.set(str(_main_mod.AIR_DENSITY))
            self.velocity_var.set(str(_main_mod.VELOCITY))
            self.viscosity_var.set(str(_main_mod.VISCOSITY))

            # Show defaults as reference labels
            defaults = {
                "span": _main_mod.SPAN,
                "chord": _main_mod.CHORD,
                "density": _main_mod.AIR_DENSITY,
                "velocity": _main_mod.VELOCITY,
                "viscosity": _main_mod.VISCOSITY,
            }
            for key, val in defaults.items():
                lbl = self._phys_default_labels.get(key)
                if lbl:
                    lbl.config(text=f"(default: {val})")

            self._update_derived_values()

            # XY data dir
            self.xy_var.set(str(_main_mod.XY_DATA_SOURCE_DIR))

            # Schema
            from config import ACTIVE_SCHEMA
            self.schema_var.set(ACTIVE_SCHEMA)
        except Exception as exc:
            self._log(f"⚠ Could not load defaults from main.py: {exc}\n")

    # ─── Button Callbacks ────────────────────────────────────────────────

    def _add_source(self):
        folder = filedialog.askdirectory(title="Select Data Source Folder")
        if folder:
            self.src_listbox.insert("end", folder)

    def _remove_source(self):
        for idx in reversed(self.src_listbox.curselection()):
            self.src_listbox.delete(idx)

    def _clear_sources(self):
        self.src_listbox.delete(0, "end")

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_var.set(folder)

    def _browse_xy(self):
        folder = filedialog.askdirectory(title="Select XY Data Source Directory")
        if folder:
            self.xy_var.set(folder)

    def _update_trim_label(self, _):
        pct = int(self.trim_var.get())
        self.trim_label.config(text=f"{pct}%")

    def _clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _update_derived_values(self):
        """Recompute and display Reference Area, Q×A, and Reynolds Number."""
        try:
            span = float(self.span_var.get())
            chord = float(self.chord_var.get())
            density = float(self.density_var.get())
            velocity = float(self.velocity_var.get())
            viscosity = float(self.viscosity_var.get())

            ref_area = span * chord
            q = 0.5 * density * velocity ** 2
            q_times_a = q * ref_area
            re = (density * velocity * chord) / viscosity

            self._derived_label.config(
                text=f"Ref Area: {ref_area:.5f} m²   |   Q×A: {q_times_a:.4f} N   |   Re: {re:,.0f}"
            )
        except (ValueError, ZeroDivisionError):
            self._derived_label.config(text="(enter valid physics values to see derived quantities)")

    # ─── Build config dict from GUI fields ───────────────────────────────

    def _build_config(self) -> dict | None:
        """Validate inputs and return a config dict, or None on failure."""
        errors = []

        # Data sources
        sources = list(self.src_listbox.get(0, "end"))
        if not sources:
            errors.append("At least one data source folder is required.")
        data_sources = [Path(s) for s in sources]

        # Output dir
        out_dir = self.output_var.get().strip()
        if not out_dir:
            errors.append("Output directory is required.")

        # AoA filter
        aoa_text = self.aoa_var.get().strip()
        aoa_filter = []
        if aoa_text:
            try:
                aoa_filter = [int(x.strip()) for x in aoa_text.split(",") if x.strip()]
            except ValueError:
                errors.append("AoA Filter must be comma-separated integers (e.g. 5,6,7).")

        # Physics
        physics_fields = {
            "Span": self.span_var,
            "Chord": self.chord_var,
            "Air Density": self.density_var,
            "Velocity": self.velocity_var,
            "Viscosity": self.viscosity_var,
        }
        physics = {}
        for name, var in physics_fields.items():
            try:
                val = float(var.get())
                if val <= 0:
                    errors.append(f"{name} must be a positive number.")
                physics[name] = val
            except ValueError:
                errors.append(f"{name} must be a valid number.")

        if errors:
            messagebox.showerror("Validation Errors", "\n".join(errors))
            return None

        span = physics["Span"]
        chord = physics["Chord"]
        air_density = physics["Air Density"]
        velocity = physics["Velocity"]
        viscosity = physics["Viscosity"]

        ref_area = span * chord
        dyn_pressure = 0.5 * air_density * velocity ** 2
        q_times_a = dyn_pressure * ref_area
        reynolds = (air_density * velocity * chord) / viscosity

        return {
            "data_sources": data_sources,
            "output_dir": Path(out_dir),
            "config_extraction_method": self.extraction_var.get(),
            "comparison_mode": self.mode_var.get(),
            "active_schema": self.schema_var.get(),
            "aoa_filter": aoa_filter or None,
            "xy_data_source_dir": Path(self.xy_var.get().strip()) if self.xy_var.get().strip() else None,
            "num_iterations": self.iter_var.get(),
            "run_convergence_analysis": self.conv_var.get(),
            "convergence_max_trim": self.trim_var.get() / 100.0,
            "convergence_num_tests": self.tests_var.get(),
            "graph_max_cov": self.cov_var.get(),
            "span": span,
            "chord": chord,
            "air_density": air_density,
            "velocity": velocity,
            "viscosity": viscosity,
            "reference_area": ref_area,
            "dynamic_pressure": dyn_pressure,
            "q_times_a": q_times_a,
            "reynolds_number": reynolds,
        }

    # ─── Run / Stop ──────────────────────────────────────────────────────

    def _on_run(self):
        config = self._build_config()
        if config is None:
            return

        self._clear_console()
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._running = True

        def worker():
            # Redirect stdout / stderr to the GUI console
            old_stdout, old_stderr = sys.stdout, sys.stderr
            redir = QueueWriter(self._log_queue)
            sys.stdout = redir
            sys.stderr = redir
            try:
                from main import main
                main(config=config)
            except Exception as exc:
                import traceback
                traceback.print_exc(file=redir)
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr
                self._running = False
                # Schedule UI update on the main thread
                self.after(0, self._on_worker_done)

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def _on_stop(self):
        """
        There is no clean way to kill a running thread in Python.
        This simply flags it so the user knows; the thread will finish its
        current operation and then the UI resets.
        """
        self._running = False
        self._log("\n⚠ Stop requested — processing will halt after the current step.\n")
        self.stop_btn.configure(state="disabled")

    def _on_worker_done(self):
        self.run_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._log("\n── Processing finished ──\n")
        self._populate_results()
        self._auto_show_key_graphs()

    # ─── Results viewer helpers ──────────────────────────────────────────

    def _populate_results(self):
        """Scan the output directory for generated files and populate the tree."""
        self.results_tree.delete(*self.results_tree.get_children())
        self._preview_label.config(image="", text="Select a graph to preview")
        self._preview_photo = None

        out_dir = self.output_var.get().strip()
        if not out_dir or not Path(out_dir).exists():
            return

        out_path = Path(out_dir)

        # Collect image files by category
        categories = {
            "Coefficient Graphs": out_path / "coefficient_graphs",
            "Convergence Analysis": out_path / "convergence_analysis",
            "Extra Plots (Cp/Y+/Cf)": out_path / "Extra_Plots",
        }

        for cat_name, cat_path in categories.items():
            if not cat_path.exists():
                continue
            png_files = sorted(cat_path.rglob("*.png"))
            if not png_files:
                continue

            cat_id = self.results_tree.insert("", "end", text=f"📁 {cat_name} ({len(png_files)})",
                                              open=False)
            for png in png_files:
                # Show relative path from category root for readability
                rel = png.relative_to(cat_path)
                self.results_tree.insert(cat_id, "end", text=str(rel),
                                         values=(str(png),),  # stash absolute path
                                         tags=("file",))

        # Also list Excel and text summary files
        summary_files = sorted(out_path.glob("SUMMARY_*"))
        if summary_files:
            cat_id = self.results_tree.insert("", "end", text=f"📄 Summary Files ({len(summary_files)})",
                                              open=True)
            for sf in summary_files:
                self.results_tree.insert(cat_id, "end", text=sf.name,
                                         values=(str(sf),), tags=("file",))

    def _get_selected_path(self) -> Path | None:
        """Return the absolute path of the currently selected tree item, or None."""
        sel = self.results_tree.selection()
        if not sel:
            return None
        vals = self.results_tree.item(sel[0], "values")
        if vals:
            return Path(vals[0])
        return None

    def _on_result_select(self, _event=None):
        """Show a preview of the selected image file."""
        fpath = self._get_selected_path()
        if not fpath or not fpath.exists():
            return

        if not _HAS_PIL or fpath.suffix.lower() not in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
            self._preview_label.config(image="", text=fpath.name)
            self._preview_photo = None
            return

        try:
            img = Image.open(fpath)
            # Fit into a reasonable preview size
            max_w, max_h = 600, 450
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._preview_label.config(image=photo, text="")
            self._preview_photo = photo  # prevent garbage collection
        except Exception:
            self._preview_label.config(image="", text=f"Cannot preview: {fpath.name}")
            self._preview_photo = None

    def _show_preview(self, fpath: Path):
        """Show an image file in the preview panel."""
        if not _HAS_PIL or not fpath.exists():
            return
        try:
            img = Image.open(fpath)
            max_w, max_h = 600, 450
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._preview_label.config(image=photo, text="")
            self._preview_photo = photo
        except Exception:
            self._preview_label.config(image="", text=f"Cannot preview: {fpath.name}")
            self._preview_photo = None

    # ─── Slideshow navigation ────────────────────────────────────────────

    def _set_slideshow(self, images: list[Path]):
        """Set the slideshow images and display the first one."""
        self._slideshow = images
        self._slide_idx = 0
        if images:
            self._show_slide()
        else:
            self._preview_label.config(image="", text="No key graphs found")
            self._preview_photo = None
            self._slide_info.config(text="")
            self._prev_btn.config(state="disabled")
            self._next_btn.config(state="disabled")

    def _show_slide(self):
        """Display the current slideshow image and update controls."""
        if not self._slideshow:
            return
        idx = self._slide_idx
        fpath = self._slideshow[idx]
        self._show_preview(fpath)
        self._slide_info.config(text=f"{idx + 1}/{len(self._slideshow)}  —  {fpath.name}")
        self._prev_btn.config(state="normal" if idx > 0 else "disabled")
        self._next_btn.config(state="normal" if idx < len(self._slideshow) - 1 else "disabled")

    def _slide_prev(self):
        if self._slide_idx > 0:
            self._slide_idx -= 1
            self._show_slide()

    def _slide_next(self):
        if self._slide_idx < len(self._slideshow) - 1:
            self._slide_idx += 1
            self._show_slide()

    # ─── Auto-show key graphs after processing ───────────────────────────

    def _auto_show_key_graphs(self):
        """Collect key graphs and start a slideshow automatically."""
        out_dir = self.output_var.get().strip()
        if not out_dir or not Path(out_dir).exists():
            return

        out_path = Path(out_dir)
        mode = self.mode_var.get()
        key_images: list[Path] = []

        # 1. Combined CL/CD or Aerodynamic Summary plots
        coeff_dir = out_path / "coefficient_graphs"
        if coeff_dir.exists():
            if mode == "default":
                # Single configs — look for Combined_CL_CD or Aerodynamic_Summary in Single/
                for png in sorted(coeff_dir.rglob("*_Aerodynamic_Summary.png")):
                    key_images.append(png)
                if not key_images:
                    for png in sorted(coeff_dir.rglob("*_Combined_CL_CD.png")):
                        key_images.append(png)
            else:
                # Comparison mode — look in Comparison/ folder
                comp_dir = coeff_dir / "Comparison"
                if comp_dir.exists():
                    for png in sorted(comp_dir.rglob("*_Aerodynamic_Summary.png")):
                        key_images.append(png)
                    if not key_images:
                        for png in sorted(comp_dir.rglob("*_Combined_CL_CD.png")):
                            key_images.append(png)

        # 2. Pressure coefficient plots for AoA 5, 10, 15, 20
        cp_dir = out_path / "Extra_Plots" / "pressure_coefficient"
        if cp_dir.exists():
            target_aoas = ["AoA_5", "AoA_10", "AoA_15", "AoA_20"]
            for png in sorted(cp_dir.rglob("Cp_*.png")):
                if any(aoa in png.name for aoa in target_aoas):
                    key_images.append(png)

        if key_images:
            self._log(f"\n📊 Auto-displaying {len(key_images)} key graph(s). Use ◀/▶ to navigate.\n")
            self._set_slideshow(key_images)
        else:
            self._log("\n📊 No key graphs found to auto-display.\n")

    def _open_selected_file(self):
        """Open the selected file in the system default application."""
        fpath = self._get_selected_path()
        if fpath and fpath.exists():
            os.startfile(str(fpath))

    def _open_output_folder(self):
        """Open the output directory in Windows Explorer."""
        out_dir = self.output_var.get().strip()
        if out_dir and Path(out_dir).exists():
            subprocess.Popen(["explorer", str(Path(out_dir))])

    # ─── Console helpers ─────────────────────────────────────────────────

    def _log(self, text: str):
        self.console.configure(state="normal")
        self.console.insert("end", text)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _poll_log_queue(self):
        """Drain the log queue and append to the console widget."""
        while True:
            try:
                text = self._log_queue.get_nowait()
            except queue.Empty:
                break
            self._log(text)
        self.after(100, self._poll_log_queue)


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CFDApp()
    app.mainloop()
