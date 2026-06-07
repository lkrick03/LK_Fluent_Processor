# Output — Fluent Journal & Visualization Exporters (AoA Sweep)

**Author**: Luke Krick  
**Last Updated**: May 2026

## Overview

This directory contains scripts for **generating ANSYS Fluent journal files** and **post-processing visualization exports** for **Angle-of-Attack (AoA) sweep** simulations. These are the AoA-domain counterparts to the velocity/Mach scripts in `Data_Processing_Velocity/`.

## Scripts

### 1. `jou_exporter.py` — Fluent Journal Generator (AoA Sweep)

Generates `.jou` files that automate AoA sweep simulations in ANSYS Fluent, including boundary condition setup, solving, and saving.

```powershell
python jou_exporter.py
```

**Key settings** (edit the CONFIGURATION section at the top):

| Setting | Description | Example |
|---------|-------------|---------|
| `AOA_MODE` | How AoA values are specified | `"Range"`, `"List"`, `"MultiRange"` |
| `AOA_LIST` | Explicit list of AoA values | `[0, 0.5, 1, 1.5, 2, ...]` |
| `AOA_START/END/STEP` | Range mode parameters | `5` to `20`, step `1.0` |
| `V_MAG` | Freestream velocity (m/s) | `14.3773` (Re 300,000) |
| `BASE_OUTPUT_DIR` | HPC output path (Linux) | `/home/<HPC_USERNAME>/directories/...` |
| `ITERATIONS` | Solver iterations per AoA | `1200` |
| `TEST_MODE` | Apply BCs without solving | `True` / `False` |

**Zone Logic**: The script supports zone-based boundary condition overrides for specific AoA ranges. For example, negative AoAs beyond -4° can flip inlet/outlet assignments to handle reversed flow.

**Output**: A single `.jou` file that Fluent reads to sweep through all AoA values automatically.

---

### 2. `jou_post_exporter.py` — Post-Processing Journal (XY Data, Residuals, Pathlines)

Generates journal files that batch-load **completed** simulations and export surface data.

```powershell
python jou_post_exporter.py
```

**What it exports**:
- **XY plots**: Pressure coefficient (Cp), Y+ (wall distance), Skin friction coefficient
- **Residuals**: Full convergence history exported via Scheme scripting
- **Pathlines** (optional): Velocity-magnitude pathline data (`.fvp` files)

**How it works**:
1. Auto-discovers `AoA_*` folders (or uses a manual list)
2. Generates TUI commands to load each case file
3. Exports `.xy` data for each variable on airfoil surfaces
4. Optionally exports residual history and pathline data

---

### 3. `jou_contour_exporter.py` — Contour Plot Journal (Fluent TUI)

Generates journal files that create **contour plot images** directly in Fluent.

```powershell
python jou_contour_exporter.py
```

**Features**:
- Exports contour images (PNG/JPEG/TIFF) for configurable variables
- Supports custom camera views loaded from a `.vw` file
- Optional camera rotation to compensate for AoA
- Auto-creates cross-sectional planes for 3D domains
- Configurable resolution (default: 1920×1080)

**Variables**: Static Pressure, Cp, Velocity Magnitude, Skin Friction Coefficient

---

### 4. `paraview_contour_exporter.py` — ParaView Automated Contour Export

Loads Fluent `.cas.h5` files directly into **ParaView** for higher-quality contour visualization.

> **Must be run with `pvpython.exe`, NOT standard Python!**

```powershell
& "C:\Program Files\ParaView 6.1.0\bin\pvpython.exe" paraview_contour_exporter.py
```

**Features**:
- Auto-discovers `AoA_*` folders
- Smooths Fluent cell data → point data for gradient visualization
- Calculates Velocity Magnitude and Mach Number from Fluent primitives
- Multiple custom camera views per variable
- AoA-tracking camera (vertical shift to follow airfoil rotation)
- Color range locking for consistent coloring across AoAs
- Optional streamline rendering with configurable seed lines
- Airfoil counter-rotation for horizontal presentation

---

### 5. `paraview_gif_maker.py` — Animated GIF Creator (AoA)

Compiles ParaView contour PNGs into animated GIFs sweeping through AoA.

```powershell
python paraview_gif_maker.py
```

**Features**:
- Groups frames by variable + camera view
- Supports multiple source directories
- "Highest Version Wins" deduplication (when multiple config versions exist)
- Configurable frame duration (default: 250ms)

---

### 6. `contour_comparison.py` — Side-by-Side Contour Comparison

Stitches contour images from **two different simulations** side-by-side for direct visual comparison.

```powershell
python contour_comparison.py
```

**Features**:
- Compares two sets of simulations (e.g., "No Grid" vs "With Grid")
- Multiple source directories per side with version deduplication
- 16:9 output canvas with labeled panels
- Auto-discovers shared AoA values between both sides
- Creates animated GIFs of the comparison
- Paper mode (omit labels for publication-ready images)

---

### Jupyter Notebooks

| Notebook | Purpose |
|----------|---------|
| `jou_file.ipynb` | Interactive journal file prototyping |
| `jou_v2.ipynb` | Refined journal generation (V2) |

## Typical Workflow

```
1. Set up simulation    →  jou_exporter.py         →  .jou file
2. Run on HPC           →  Fluent reads .jou        →  Case/Data files
3. Extract XY data      →  jou_post_exporter.py     →  .xy + residual files
4. Generate contours    →  paraview_contour_exporter →  PNG images
5. Create GIFs          →  paraview_gif_maker.py     →  Animated GIFs
6. Compare simulations  →  contour_comparison.py     →  Side-by-side images
```

## Dependencies

- `numpy` (journal generators)
- `pillow` (GIF maker, contour comparison)
- **ParaView** (`pvpython.exe`) — for `paraview_contour_exporter.py` only
- **ANSYS Fluent** — to execute generated `.jou` files
