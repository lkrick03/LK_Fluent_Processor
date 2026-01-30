# CFD Data Processing Workflow

**Author**: Luke K.  
**Last Updated**: January 2026

## Overview
This Python workflow automates the processing of Fluent CFD simulation data. It loads lift/drag force files, applies Angle of Attack (AoA) corrections, performs convergence analysis, and generates publication-ready Excel summaries and coefficient graphs.

## Quick Start
1.  Open `main.py`.
2.  Update `DATA_SOURCES` with the paths to your simulation folders.
3.  Set your desired `COMPARISON_MODE` (see below).
4.  Run the script: `python main.py`.

## Key Features

### 1. Comparison Modes
Control how data is grouped and analyzed by changing `COMPARISON_MODE` in `main.py`:

| Mode | Description | Output |
| :--- | :--- | :--- |
| **`default`** | Standard processing. Loads the highest version of each simulation. | Data Summary, Coefficients, Graphs (by Turbulence Model). |
| **`turbulence`** | Compare different turbulence models (SST vs RNG vs RSM). | "Turbulence Comparison" sheet + Overlaid Graphs. |
| **`grid`** | Compare "No Grid" vs "With Grid". | "Grid Comparison" sheet + Overlaid Graphs. |
| **`version`** | Compare different versions (V3 vs V4) of the same config. | "Version Comparison" sheet (auto-detected). |

### 2. Intelligent File Selection
If a folder contains multiple force files (e.g., from restarts like `lift_force-1.txt` and `lift_force.txt`):
*   **Logic**: The script automatically picks the **newest file** (based on "Last Modified" timestamp).
*   **Fallback**: If timestamps are identical, it picks the largest file.
*   **Feedback**: A `[WARNING]` is printed in the console confirming which file was selected.

### 3. Automatic Sorting
All outputs (Excel sheets, Text Summaries, Graphs) are strictly sorted by:
1.  **Simulation Family** (Geometry → Mesh → Turbulence)
2.  **Angle of Attack** (Numeric increment)

### 4. Convergence Analysis
*   Set `RUN_CONVERGENCE_ANALYSIS = True` to enable.
*   The system analyzes the tail end of your data to recommend the optimal "trim" point for stable mean/COV values.

## Configuration
All user-configurable settings are at the top of `main.py`:
*   `DATA_SOURCES`: List of input directories.
*   `OUTPUT_DIR`: Where results will be saved.
*   `COMPARISON_MODE`: Controls grouping logic.
*   `NUM_ITERATIONS`: Number of iterations to use for averaging (default 150).

## Dependencies
*   `numpy`
*   `pandas`
*   `matplotlib`
*   `openpyxl`
