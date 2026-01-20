# Copilot Instructions for CFD Data Processing Thesis

## Project Overview

This is a CFD simulation data processing pipeline for aerodynamic analysis of NACA airfoils. The project consolidates four Jupyter notebooks into a modular Python codebase that processes lift/drag simulation data, analyzes convergence behavior, generates Excel summaries, and creates coefficient graphs.

**Key Deliverables:**
- Processed CFD data with AoA corrections applied
- Convergence analysis to optimize data statistics
- Excel reports with turbulence model comparisons
- Aerodynamic coefficient graphs (C_L, C_D, drag polar curves)

## Architecture

### Core Components

**`main.py` (458 lines)** - Single-entry execution script
- Lines 16-75: **Critical** - All user configuration in one place
  - `BASE_PATH` / `OUTPUT_DIR` for data location
  - `CONFIG_EXTRACTION_METHOD`: 'case_file' or 'folder' (config parsing strategy)
  - `POSITION_MAP` and `VALUE_MAPPINGS`: Decode config strings (e.g., "4.3.1.3.G" → geometry/mesh/turbulence/version/grid)
  - `NUM_ITERATIONS`: Last N iterations for statistics (default 150)
  - `RUN_CONVERGENCE_ANALYSIS`: Boolean to enable/disable Part 2
  - `CONVERGENCE_MAX_TRIM`: Max fraction to trim (0.8 = 80% of data)
- Runs 4-part workflow in sequence:
  1. **Part 1** (lines 103-175): Load raw CFD data and save processed_data.pkl
  2. **Part 2** (lines 177-334): Optional convergence analysis with percentage-based trim testing
  3. **Part 3** (lines 336-368): Generate Excel workbook (3-4 sheets depending on convergence)
  4. **Part 4** (lines 370-415): Create coefficient graphs organized by turbulence model

**`cfd_functions.py` (1129 lines)** - Reusable functions library

#### Data Loading (`load_lift_drag_data`)
- Recursively walks `BASE_PATH` looking for `lift_force_*.txt` and `drag_force_*.txt` files
- Extracts config from case files (`.cas` / `.cas.h5`) or folder structure
- **AoA Correction** (lines 105-120): Rotates lift/drag vectors by angle using `cos(θ)` / `sin(θ)`
  - Raw forces in body frame → true aerodynamic frame
  - Critical for accuracy; do not skip

#### Configuration Parsing
- **POSITION_MAP**: Maps config string positions to semantic fields (geometry/mesh/turbulence/version/grid)
  - Example: "4.3.1.3.G" split by '.' → `[4, 3, 1, 3, G]` → positions 0-4 indexed
- **VALUE_MAPPINGS**: Translates numeric codes to human-readable names
  - Geometry: `3 → '2414_006_003'`, `4 → '2414_006_004'`
  - Mesh: `1 → 'Coarse'`, `2 → 'Medium'`, `3 → 'Baseline'`, etc.
  - Turbulence: `1 → 'SST'`, `2 → 'RNG'`, `3 → 'RSM'`
  - Grid: `'NG' → 'No Grid'`, `'G' → 'With Grid'`
- Must be updated in `main.py` if simulation configs change

#### Convergence Analysis (`analyze_convergence`)
- **Percentage-based trimming** (not iteration counts)
  - Parametrize: `min_trim=0` (no data removed) to `max_trim=0.8` (80% removed)
  - Test `num_tests=20` evenly-spaced trim values
  - For each trim point, calculate: mean, std dev, COV (coefficient of variation)
- Returns dict with keys: `iterations_removed`, `iterations_used`, `mean`, `std_dev`, `cov`
- Picks optimal trim as **minimum COV** (minimum uncertainty)

#### Excel Sheet Creation
- `create_data_summary_sheet()`: Summary stats for each config/AoA
- `create_turbulence_comparison_sheet()`: Side-by-side comparison of turbulence models
- `create_coefficients_sheet()`: Normalized coefficients (C_L, C_D)
- `create_optimized_statistics_sheet()`: Only generated if convergence ran (Part 2)
- All use `apply_excel_formatting()` for professional appearance

#### Coefficient Graphs (`create_coefficient_graphs`)
- Organized hierarchically: `coefficient_graphs / {turbulence_model} / {config} /`
- Each config generates 4 plots:
  1. **C_L_vs_AoA.png** - Lift coefficient vs angle of attack
  2. **C_D_vs_AoA.png** - Drag coefficient vs angle of attack
  3. **Drag_Polar.png** - C_L vs C_D (with AoA annotations)
  4. **C_L_C_D_Combined.png** - Side-by-side C_L and C_D
- Uses coefficient: $C = \frac{\text{Force}}{q \times A}$ where $q = 0.5 \rho V^2$ (dynamic pressure)

### Data Flow

```
CFD Raw Files (lift_force_*.txt, drag_force_*.txt)
           ↓
load_lift_drag_data() → extract config/AoA → AoA correction → processed_data.pkl
           ↓
[Optional] analyze_convergence() → convergence_results.pkl
           ↓
Excel sheet creation + Coefficient graphs
```

### Output Files

**Generated in OUTPUT_DIR:**
- `processed_data.pkl` - Full dataset after AoA correction
- `convergence_results.pkl` - Convergence analysis (if Part 2 enabled)
- `SUMMARY_{config}.xlsx` - Excel report (3-4 sheets)
- `processed_data/` - Individual lift/drag text files per config
- `convergence_analysis/` - Convergence plots and optimized data
- `coefficient_graphs/` - Aerodynamic plots organized by turbulence

## Developer Workflows

### Running the Pipeline

```powershell
# From Data Processing/ directory
python main.py
```

**Expected runtime:** 5-15 minutes depending on dataset size and convergence analysis complexity.

**Verify outputs:** Check `OUTPUT_DIR` for all expected files (see above).

### Debugging Failed Runs

1. **Check BASE_PATH**: Ensure it exists and contains the expected folder structure with `AoA_*` subfolders
2. **Verify file format**: Raw CFD files must be named `lift_force_*.txt` and `drag_force_*.txt`
3. **Validate config parsing**:
   - Check if case files (`.cas` / `.cas.h5`) are readable
   - Or verify folder names match pattern (e.g., "4.3.1.3.G")
4. **Review logs in console**: Each part prints progress; look for error messages

### Adding New Configurations

**To process a new airfoil or simulation:**
1. Update `POSITION_MAP` if config format differs
2. Add mappings to `VALUE_MAPPINGS` (geometry/mesh/turbulence codes)
3. Update `COMPARISON_CONFIGS` if needed for grouped analysis
4. Update `BASE_PATH` and `OUTPUT_DIR` paths
5. Adjust `SPAN`, `CHORD`, `AIR_DENSITY`, `VELOCITY` if test conditions changed

## Project Conventions

### Data Structure Rules
- **Config strings**: Dot-separated (e.g., "4.3.1.3.G") - parse using `POSITION_MAP`
- **AoA folders**: Named "AoA_{degrees}" (e.g., "AoA_10", "AoA_-5")
- **Force files**: Always `lift_force_*.txt` and `drag_force_*.txt` in same directory
- **Pickle files**: Store full dataset snapshots for reproducibility (loaded in notebooks)

### Naming Conventions
- **Excel sheets**: PascalCase (e.g., `Data_Summary`, `Turbulence_Comparison`)
- **Graph directories**: Lowercase with underscores (e.g., `coefficient_graphs`)
- **Output summaries**: `SUMMARY_{config}.txt` / `SUMMARY_{config}.xlsx`

### Statistical Approach
- **Primary metric**: COV (Coefficient of Variation) = StdDev / Mean × 100%
  - Lower COV = more stable, preferred for aerodynamic analysis
- **Data trimming**: Remove leading iterations (transient effects) to improve convergence
  - Do NOT filter outliers; use percentage-based trimming
- **Last N iterations**: Default 150 for statistics if convergence not run; **configurable**

## Testing & Validation

### Sanity Checks for New Code

1. **AoA correction preserved**: Verify rotated forces are sensible (e.g., lift < drag at stall angles)
2. **Config parsing**: Print a few parsed configs to verify geometry/mesh/turbulence values
3. **Excel formatting**: Open XLSX and verify headers/colors/borders applied correctly
4. **Graph generation**: Spot-check 1-2 graphs for reasonable trends (e.g., C_L increases with AoA until stall)

### Key Test Scenarios

- **Different config formats**: Test 'case_file' vs 'folder' extraction methods
- **Convergence edge cases**: Very small datasets, all trim values same
- **Missing AoA folders**: Gracefully skip and report in logs
- **Excel special chars**: Config names with hyphens/spaces in sheet names

## Important Caveats

1. **Path handling**: Project uses both relative and absolute paths; ensure `OUTPUT_DIR` is writable
2. **Large datasets**: Processing can consume significant RAM for 1000+ configurations; monitor memory
3. **Matplotlib backends**: Some systems may need to configure backend for graph generation
4. **Excel formula dependencies**: Sheets may have embedded formulas; preserve when editing
5. **AoA correction critical**: Lifting-line theory depends on accurate frame rotation; do not skip

## References

- **aerodynamic coefficients**: $C_L = \frac{L}{q \times A}$, $C_D = \frac{D}{q \times A}$ where $q = \frac{1}{2}\rho V^2$
- **convergence metric**: COV indicates solution stability; aim for <5% for production data
- **NACA 2414**: 4-digit airfoil series (2=max camber/chord, 4=position, 14=max thickness)
