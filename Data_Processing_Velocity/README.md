# CFD Data Processing — Velocity Sweep

**Author**: Luke Krick  
**Last Updated**: May 2026

## Overview

This module processes **velocity/Mach sweep** CFD simulation data from ANSYS Fluent. It is the velocity-domain counterpart to the `Data Processing` folder (which handles Angle-of-Attack sweeps). The pipeline loads drag force files from Mach-numbered directories, computes statistics, runs convergence analysis, and generates Excel summaries and coefficient graphs.

## Quick Start

```powershell
# 1. Recreate the virtual environment (if needed)
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt

# 2. Edit the ACTIVE_PRESET in main_vel.py (or step1/step2 directly)
# 3. Run the full pipeline
python main_vel.py
```

## Pipeline Architecture

The pipeline is split into two steps for efficiency — Step 1 does the heavy parsing once, then Step 2 can quickly regenerate graphs without re-loading raw data.

```
Raw Fluent Data (Mach_*/drag_force_*.txt)
          │
          ▼
  ┌──────────────────┐
  │  Step 1: Process  │  ← step1_process_vel.py
  │  - Load drag data │
  │  - Convergence    │
  │  - Save .pkl      │
  └────────┬─────────┘
           │  pipeline_state.pkl
           ▼
  ┌──────────────────┐
  │  Step 2: Output   │  ← step2_generate_outputs_vel.py
  │  - Excel summary  │
  │  - Coeff. graphs  │
  │  - Presentation   │
  └──────────────────┘
```

### `main_vel.py` — Consolidated Runner

Runs both Step 1 and Step 2 sequentially. Set `ACTIVE_PRESET` to the name of a preset defined in `mvel_config.py`.

### `step1_process_vel.py` — Data Loading & Analysis

- Loads raw drag force files from `Mach_*` directories
- Extracts configuration metadata from `.cas.h5` filenames
- Runs convergence analysis (trim optimization for stable COV)
- Supports **merging** previously-processed `.pkl` files for comparison runs
- Saves all state to `pipeline_state.pkl`

### `step2_generate_outputs_vel.py` — Excel & Graphs

- Loads `pipeline_state.pkl` from Step 1
- Generates Excel workbook with:
  - Data Summary sheet
  - Coefficients sheet (C_D)
  - Turbulence/Version/Grid comparison sheets (depending on mode)
  - Optimized statistics (from convergence analysis)
- Creates coefficient graphs (normal + presentation mode)

## Configuration — `mvel_config.py`

All settings are centralized here:

### Naming Schemas

| Schema | Example | Fields |
|--------|---------|--------|
| `5-part` | `1.2.1.3.NG` | aoa.mesh.turbulence.version.grid |
| `4-part` | `1.2.1.2` | aoa.mesh.turbulence.version |

Set `ACTIVE_SCHEMA` to match your data format.

### Value Mappings

Maps numeric config parts to human-readable labels:
- **aoa**: 1→'0°', 2→'5°', 3→'10°', etc.
- **mesh**: 1→'4V6', 2→'4-inch-half-fin', etc.
- **turbulence**: 1→'SST', 2→'K-Epsilon Standard', 3→'RSM'
- **grid**: 'NG'→'No Brake', 'G'→'With Brake'

### Run Presets

Pre-configured runs are defined in `RUN_PRESETS`. Two types:

| Type | Key | Description |
|------|-----|-------------|
| **Single** | `data_sources` | Points to raw `unprocessed_data` directories |
| **Comparison** | `processed_sources` | Points to existing `pipeline_state.pkl` files to merge |

Example:
```python
ACTIVE_PRESET = "O_single_1.2.1.2.NG"  # in main_vel.py
```

### Comparison Modes

| Mode | Description |
|------|-------------|
| `single` | Standard processing of one configuration |
| `version` | Compare different versions (e.g., V6 vs V7) |
| `grid` | Compare No-Brake vs With-Brake |
| `turbulence` | Compare different turbulence models |

## Utility Scripts

### `vel_jou_export.py` — Fluent Journal Generator (Mach Sweep)

Generates `.jou` files for ANSYS Fluent to automate Mach sweep simulations on HPC clusters.

```powershell
python vel_jou_export.py
```

**Key settings** (edit the CONFIGURATION section):
- `MACH_MODE`: "Range", "List", or "MultiRange"
- `BASE_OUTPUT_DIR`: HPC output path
- Boundary condition zones and TUI command strings
- Post-processing variables (Cp, Y+, Skin Friction) exported inline

### `vel_paraview_exporter.py` — ParaView Contour Export

Automatically loads Fluent `.cas.h5` files into ParaView and exports high-resolution contour plots.

> **Must be run with `pvpython.exe`, NOT standard Python!**

```powershell
& "C:\path\to\pvpython.exe" vel_paraview_exporter.py
```

**Features**:
- Auto-discovers `Mach_*` folders
- Custom camera views (center, nose cone, fins zoom)
- Color range locking for GIF consistency
- Velocity magnitude and Mach number calculated from Fluent primitives
- Optional streamline rendering

### `vel_gif_maker.py` — Animated GIF Creator

Compiles ParaView contour PNGs into animated GIFs across Mach numbers.

```powershell
python vel_gif_maker.py
```

- Groups frames by variable and camera view
- Supports multiple source directories with "Highest Version Wins" deduplication
- Configurable frame duration

### `merge_exporter.py` — One-Time Script Merger

A utility script that was used to merge post-processing functionality into `vel_jou_export.py`. **Not needed for normal operation.**

### Other Files

| File | Purpose |
|------|---------|
| `swap_terms.py` | One-off text substitution utility |
| `remove_extra_graphs.py` | Cleanup script for old graph files |
| `write_headers.py` | Utility for inspecting data file headers |
| `headers_output.txt` | Reference output from header inspection |

## Dependencies

- `numpy`
- `pandas`
- `matplotlib`
- `openpyxl`
- `pillow` (for GIF maker)
- **ParaView** (for `vel_paraview_exporter.py` only — run via `pvpython.exe`)
