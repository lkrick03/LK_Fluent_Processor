# GRID-FINS — CFD Data Processing Toolkit

**Author**: Luke Krick  
**Group F.L.U.I.D. — Liberty University**  
**Last Updated**: June 2026

---

## What Is This?

This repository contains Python scripts that **automate the processing of CFD (Computational Fluid Dynamics) simulation data** from ANSYS Fluent. In simple terms: after you run a rocket simulation on the HPC cluster, these scripts take the raw output files and turn them into organized Excel spreadsheets, coefficient graphs, contour images, and animated GIFs — all without you having to open Excel or do math by hand.

The simulations study **grid fins** (the waffle-shaped fins you see on SpaceX Falcon 9 boosters) and how they perform across different flight speeds and angles of attack.

---

## 🚀 Rocketry Team — Start Here

**The folder you care about most is [`Data_Processing_Velocity/`](Data_Processing_Velocity/).** This is the primary pipeline for processing Mach sweep data — i.e., how your rocket's grid fins perform at different speeds (Mach numbers).

### What does it do?

1. **Reads** the raw drag force files that Fluent outputs during a simulation
2. **Analyzes** the data for convergence (did the simulation actually settle on an answer?)
3. **Calculates** aerodynamic coefficients like drag coefficient (C_D)
4. **Exports** everything into a clean Excel workbook and publication-ready graphs

### How do I run it?

```powershell
# 1. Open a terminal and navigate to this repository
cd "path\to\this\repo"

# 2. Set up a Python virtual environment (only need to do this once)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Navigate to the velocity processing folder
cd Data_Processing_Velocity

# 4. Run the full pipeline
python main_vel.py
```

That's it! The script will process your data and output Excel files and graphs to the configured output directory.

### How do I point it at MY data?

Open [`Data_Processing_Velocity/mvel_config.py`](Data_Processing_Velocity/mvel_config.py) and look at the `RUN_PRESETS` section near the bottom. Each preset defines:

| Field | What It Means |
|-------|---------------|
| `data_sources` | The folder(s) where your raw Fluent output lives |
| `output_dir` | Where the processed Excel/graphs will be saved |
| `comparison_mode` | How to group your data (see below) |

Then open [`Data_Processing_Velocity/main_vel.py`](Data_Processing_Velocity/main_vel.py) and set `ACTIVE_PRESET` to the name of the preset you want to run.

**To create a new preset for your rocket**, copy the template at the bottom of `mvel_config.py` and fill in your paths:

```python
"<ROCKET>_single_<CONFIG>": {
    "name": "<CONFIG> Single Run (Velocity)",
    "data_sources": [
        r"C:\Users\<you>\Documents\Rocketry_CFD\<ROCKET>\directories\unprocessed_data\<CONFIG>",
    ],
    "output_dir": Path(r"C:\Users\<you>\Documents\Rocketry_CFD\<ROCKET>\directories\processed_data\<CONFIG>"),
    "comparison_mode": "single",
    "velocity_filter": []
},
```

### Comparison Modes (What They Mean)

| Mode | When to Use It |
|------|---------------|
| `single` | You just ran **one** simulation configuration and want to process it |
| `version` | You want to compare two versions of the same sim (e.g., different solver settings) |
| `grid` | You want to compare **with grid fins** vs **without grid fins** |
| `turbulence` | You want to compare different turbulence models (SST vs K-Epsilon vs RSM) |

For comparisons, you first process each individual run as `single`, then create a comparison preset that points at the `.pkl` files from each processed run. See [`Data_Processing_Velocity/README.md`](Data_Processing_Velocity/README.md) for the full details.

---

## Understanding the Config Naming System

Every simulation has a configuration string like `4.3.1.3.NG`. Here's what each part means:

```
4  .  3  .  1  .  3  .  NG
│     │     │     │     └── Grid: NG = No Brake (grid fin),  G = With Brake (grid fin)
│     │     │     └──────── Version: Solver/setup iteration (V1, V2, V3, ...)
│     │     └────────────── Turbulence Model: 1 = SST,  2 = K-Epsilon,  3 = RSM
│     └──────────────────── Mesh: Which mesh refinement level
└────────────────────────── AoA/Geometry: Angle of attack or body configuration
```

You don't need to memorize this — the scripts translate these numbers into human-readable labels automatically.

---

## Repository Structure

```
Python/
│
├── Data_Processing_Velocity/    ⭐ PRIMARY — Mach sweep data processing
│   ├── main_vel.py              ← Run this to execute the full pipeline
│   ├── mvel_config.py           ← All settings & presets go here
│   ├── step1_process_vel.py     ← Step 1: Load data, run convergence analysis
│   ├── step2_generate_outputs_vel.py  ← Step 2: Generate Excel & graphs
│   ├── mvel_functions.py        ← Core library (don't edit unless you know what you're doing)
│   ├── vel_jou_export.py        ← Generate Fluent journal files for Mach sweeps
│   ├── vel_paraview_exporter.py ← Export contour images via ParaView
│   └── vel_gif_maker.py         ← Create animated GIFs from contour images
│
├── Data Processing/             ← AoA sweep pipeline (Angle-of-Attack variant)
│   ├── main.py                  ← Same concept as main_vel.py but for AoA sweeps
│   ├── config.py                ← AoA configuration
│   ├── cfd_functions.py         ← Core library for AoA processing
│   └── gui.py                   ← Optional GUI interface
│
├── Output/                      ← Journal & visualization exporters (AoA sweep)
│   ├── jou_exporter.py          ← Generate Fluent journals for AoA sweeps
│   ├── jou_post_exporter.py     ← Export XY data, residuals, pathlines
│   ├── paraview_contour_exporter.py  ← ParaView contour export (AoA)
│   ├── paraview_gif_maker.py    ← GIF creator (AoA)
│   └── contour_comparison.py    ← Side-by-side contour comparisons
│
├── Journals/                    ← Pre-generated .jou files for Fluent
│   └── *.jou                    ← Ready-to-use journal files
│
├── Simulation Settings/         ← Simulation setup notebooks
│
├── Archived/                    ← Old/deprecated scripts (for reference only)
│
├── requirements.txt             ← Python dependencies
└── README.md                    ← You are here
```

### Which folder do I use?

- **Processing Mach/velocity sweep data** → `Data_Processing_Velocity/` ⭐
- **Processing angle-of-attack sweep data** → `Data Processing/`
- **Generating Fluent journal files for new sims** → `Output/` (AoA) or `Data_Processing_Velocity/vel_jou_export.py` (Mach)
- **Looking at pre-made journal files** → `Journals/`

---

## The Full Workflow (Big Picture)

Here's the end-to-end process for a typical grid fin study:

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. SETUP — Generate a Fluent journal file                        │
│     Script: vel_jou_export.py  (or jou_exporter.py for AoA)      │
│     Output: .jou file                                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. SIMULATE — Run the .jou file on the HPC cluster               │
│     Tool: ANSYS Fluent on HPC                                     │
│     Output: Raw drag force .txt files in Mach_* directories       │
└──────────────────────────┬──────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. PROCESS — Run the data processing pipeline              ⭐    │
│     Script: main_vel.py  (Data_Processing_Velocity/)              │
│     Output: Excel workbooks, coefficient graphs, .pkl state file  │
└──────────────────────────┬──────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. VISUALIZE (optional) — Generate contour images & GIFs         │
│     Scripts: vel_paraview_exporter.py → vel_gif_maker.py          │
│     Output: High-res contour PNGs, animated GIFs                  │
└─────────────────────────────────────────────────────────────────────┘
```

For most rocketry work, **steps 1 and 3 are the only ones you'll interact with directly.** Step 2 happens on the cluster, and Step 4 is optional for presentations.

---

## Requirements

### Python Dependencies

Install everything at once:

```powershell
pip install -r requirements.txt
```

Core packages: `numpy`, `pandas`, `matplotlib`, `openpyxl`, `pillow`

### External Software (optional)

| Software | Required For | Notes |
|----------|-------------|-------|
| **ANSYS Fluent** | Running `.jou` files | Must be run on a machine with Fluent installed (usually HPC) |
| **ParaView** | Contour image export | Run scripts with `pvpython.exe`, NOT regular Python |

---

## FAQ

**Q: I ran `main_vel.py` and it says "Loading Manual Configuration" — what's wrong?**  
A: The `ACTIVE_PRESET` in `main_vel.py` doesn't match any preset name in `mvel_config.py`. Double-check the spelling.

**Q: What's a `.pkl` file?**  
A: A Python "pickle" file — it's a snapshot of all processed data from Step 1. This lets Step 2 generate graphs quickly without re-reading all the raw simulation files.

**Q: Can I re-generate graphs without re-processing everything?**  
A: Yes! Run `step2_generate_outputs_vel.py` directly. It loads the `.pkl` file from Step 1, so it's very fast.

**Q: The script says it can't find my data files — what do I check?**  
A: Make sure the paths in your preset's `data_sources` point to a folder that contains `Mach_*` subdirectories, each with `drag_force_*.txt` files inside.

**Q: What's the difference between `Data_Processing_Velocity/` and `Data Processing/`?**  
A: `Data_Processing_Velocity/` processes **Mach sweeps** (same angle, varying speed). `Data Processing/` processes **AoA sweeps** (same speed, varying angle). For grid fin rocketry work, you'll almost always use the velocity (Mach sweep) version.
