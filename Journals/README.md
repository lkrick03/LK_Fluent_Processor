# Journals — ANSYS Fluent Journal Files

**Author**: Luke Krick  
**Last Updated**: May 2026

## Overview

This directory contains **ANSYS Fluent journal files (`.jou`)** used to automate CFD simulation sweeps. These files are fed directly to Fluent (via `File > Read > Journal` or the `/file/read-journal` TUI command) to batch-run simulations at multiple Angles of Attack (AoA).

## What is a `.jou` File?

A journal file is a text-based script written in **Fluent's Scheme/TUI language** that automates repetitive simulation tasks. Each `.jou` file in this directory:

1. Defines flow parameters (velocity, AoA range, iterations)
2. Loops through AoA values
3. Updates boundary conditions (velocity components based on AoA)
4. Runs the solver for a set number of iterations
5. Saves case/data files to organized directories

## File Naming Convention

Journal files follow the simulation configuration naming schema:

```
<geometry>.<mesh>.<turbulence>.<version>[.<grid>].jou
```

| Field | Meaning | Examples |
|-------|---------|---------|
| Geometry | Airfoil/body configuration | 1, 2, 3, 4, 5 |
| Mesh | Mesh refinement level | 1, 2, 3, 4, 5, 6 |
| Turbulence | Turbulence model | 1=SST, 2=K-Epsilon, 3=RSM |
| Version | Solver/setup version | 1, 2, 3, ... |
| Grid (optional) | Grid fin presence | NG=No Grid, G=With Grid |

### Examples

| File | Description |
|------|-------------|
| `1.1.1.jou` | Config 1.1.1, AoA sweep 5°–20° at 24.38 m/s |
| `3.1.1.NG.jou` | Config 3.1.1 without grid fins |
| `4.3.1.2.jou` | Config 4.3.1.2, includes zone overrides for complex BCs |
| `4.3.1.3.G.520.jou` | Config 4.3.1.3 with grid fins, specific velocity |
| `4.4.1.2.jou` | Config 4.4.1.2, different mesh refinement |

## How to Use

### Running on Local Machine

```
1. Open ANSYS Fluent
2. Load your mesh/case file (.cas.h5)
3. File > Read > Journal
4. Select the .jou file
5. Fluent will execute all AoA steps automatically
```

### Running on HPC Cluster

```bash
fluent 3ddp -g -t<N_CORES> -i <journal_file>.jou
```

The journal files use `mkdir -p` and Linux-style paths for HPC compatibility.

## Directory Structure

```
Journals/
├── 1.1.1.jou                  ← Current auto-generated journals
├── 2.1.1.jou
├── 3.1.1.NG.jou
├── 4.3.1.2.jou
├── 4.3.2.1.jou
├── 4.4.1.2.jou
├── 4.5.1.1.jou
├── 4.3.1.3.G.520.jou
├── 4.3.1.3.NG.520.jou
└── Journal Files (Pre-Script)/   ← Older, manually-written journals
    ├── aoa_sweep.jou
    ├── aoa_sweep_2.jou
    ├── 1.1.1.jou
    ├── ...
    └── fluenterror.log           ← Historical error log
```

### `Journal Files (Pre-Script)/`

This subfolder contains **earlier versions** of journal files that were written manually before the `jou_exporter.py` script (in `Output/`) was created to auto-generate them. They are kept for reference but the auto-generated versions in the parent directory are the current standard.

## Generating New Journals

Instead of writing `.jou` files by hand, use the automated exporters:

- **AoA sweeps**: [`Output/jou_exporter.py`](../Output/jou_exporter.py) — generates journals with configurable AoA ranges, zone logic, and boundary conditions
- **Mach sweeps**: [`Data_Processing_Velocity/vel_jou_export.py`](../Data_Processing_Velocity/vel_jou_export.py) — generates journals for velocity/Mach number sweeps

These scripts produce more robust journals with:
- Automatic velocity component calculation from AoA
- Zone-type enforcement before BC application
- Configurable multi-range AoA/Mach sequences
- Integrated post-processing (XY data, residuals, pathlines)
- Test mode (apply BCs without solving)
