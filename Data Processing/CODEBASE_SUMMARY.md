# Data Processing Codebase Summary

## Overview
This Python-based workflow automates the post-processing of ANSYS Fluent CFD simulation data. It streamlines the pipeline from raw lift/drag force files to publication-ready Excel reports and coefficient graphs, applying necessary physical corrections and statistical analyses along the way.

## Key Components

### 1. `main.py` (The Orchestrator)
*   **Configuration Hub**: Serves as the user entry point for defining data sources (`DATA_SOURCES`), output directories, and comparison modes.
*   **Workflow Control**: Manages physical constants (Span, Chord, Velocity) and drives the execution pipeline:
    1.  Load Data
    2.  Analyze Convergence (optional)
    3.  Compute Statistics
    4.  Generate Excel/Plots

### 2. `cfd_functions.py` (The Engine)
*   **Intelligent Data Loading**: Scans directories for force files, handling duplicates or restarts by prioritizing the **newest** or **largest** files to ensure data integrity.
*   **Data Correction**: Automatically applies Angle of Attack (AoA) decomposition to lift and drag forces using vectorized operations.
*   **Simulation Comparisons**: Implements logic to group and sort simulations based on the selected `COMPARISON_MODE` (`default`, `turbulence`, `grid`, `version`).
*   **Convergence Analysis**: Analyzes the "tail" of force data to recommend the optimal "trim" point—removing transient startup data to ensure stable statistical mean and coefficient of variation (COV) calculations.
*   **Reporting**: Utilizes `openpyxl` and `matplotlib` to produce formatted Excel summaries and visual comparisons.

## Key Features
*   **Comparison Modes**: flexible modes to compare turbulence models (e.g., SST vs RNG), grid configurations, or simulation versions.
*   **Robustness**: Built-in validation checks ensure folder structures and file contents are correct before processing begins.
*   **Automated Statistics**: automatically calculates mean coefficients and monitors convergence quality.

## Detailed `main.py` Analysis

### 1. User Configuration & Setup (Lines 1–67)
*   **Purpose**: Centralizes all user-adjustable settings.
*   **Key Variables**:
    *   `DATA_SOURCES`: List of input folders.
    *   `COMPARISON_MODE`: Controls grouping logic (`default`, `turbulence`, `grid`, etc.).
    *   **Physics**: Defines `SPAN`, `CHORD`, `VELOCITY` for coefficient calculations ($C_L$, $C_D$).
    *   **Convergence**: Settings for the automated trim analysis (`MAX_TRIM`, `NUM_TESTS`).

### 2. Part 1: Data Loading & Processing (Lines 85–164)
*   **Purpose**: Ingests raw data and prepares it for analysis.
*   **Actions**:
    *   Calls `load_lift_drag_data()` to scan folders and resolve duplicates.
    *   Prints a **Data Validation Report** (valid folders, skipped errors, suppressed versions).
    *   Applies data manipulations (e.g., creating "NoGrid/Grid" ratio series).
    *   Exports standardized text files to `processed_data/`.

### 3. Summary Statistics Generation (Lines 165–206)
*   **Purpose**: Provides a quick-look text summary.
*   **Actions**:
    *   Calculates Mean and COV (Coefficient of Variation) for the last `NUM_ITERATIONS` (default 150). (Look at this, how does splicing change this)
    *   Writes results to `SUMMARY_Statistics.txt`.

### 4. Part 2: Convergence Analysis (Lines 207–354)
*   **Purpose**: (Optional) intelligently finds the stable region of the simulation.
*   **Actions**:
    *   Iteratively "trims" data from the start to find the window with the lowest COV.
    *   Generates convergence plots showing how Mean/COV change with trimming.
    *   Exports "Optimized" data files (trimmed versions) to `convergence_analysis/optimized_data/`.

### 5. Part 3: Excel Outputs (Lines 355–414)
*   **Purpose**: Creates the primary deliverable for review.
*   **Actions**:
    *   Generates a multi-sheet Excel workbook.
    *   **Sheet 1**: Data Summary (Raw statistics).
    *   **Sheet 2**: Comparison Sheet (Turbulence or Grid comparisons depending on mode).
    *   **Sheet 3**: Coefficients (Calculated $C_L$, $C_D$, $L/D$).

### 6. Part 4: Coefficient Graphs (Lines 415–469)
*   **Purpose**: Visualizes the results.
*   **Actions**:
    *   Computes final aerodynamic coefficients using the best available data (Optimized or Fixed-N).
    *   Generates PNG plots for $C_L$ vs $\alpha$ and $C_D$ vs $\alpha$.
    *   Saves plots to `coefficient_graphs/`, organized by turbulence model.
