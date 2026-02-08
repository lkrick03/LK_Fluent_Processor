# Future GUI Implementation Notes

> **Status**: Planning notes for potential future development  
> **Last Updated**: February 2026

## Overview

This document outlines what a GUI for the CFD Data Processing workflow would need to configure and display. The recommended approach is to first migrate runtime settings to a YAML config file, then build a GUI that reads/writes that file.

---

## Phase 1: Config File Migration (Prerequisite)

Before building a GUI, centralize all runtime settings into `run_config.yaml`:

### Settings to Extract from `main.py`

| Setting | Current Location | Type | GUI Control |
|---------|-----------------|------|-------------|
| `DATA_SOURCES` | Lines 32-45 | List of paths | Folder picker + list |
| `OUTPUT_DIR` | Line 46 | Path | Folder picker |
| `CONFIG_EXTRACTION_METHOD` | Line 49 | String enum | Dropdown |
| `COMPARISON_MODE` | Line 57 | String enum | Dropdown |
| `NUM_ITERATIONS` | Line 60 | Integer | Spinbox |
| `RUN_CONVERGENCE_ANALYSIS` | Line 61 | Boolean | Checkbox |
| `CONVERGENCE_MAX_TRIM` | Line 62 | Float (0-1) | Slider |
| `CONVERGENCE_NUM_TESTS` | Line 63 | Integer | Spinbox |
| `SPAN` | Line 66 | Float | Number input |
| `CHORD` | Line 67 | Float | Number input |
| `AIR_DENSITY` | Line 68 | Float | Number input |
| `VELOCITY` | Line 69 | Float | Number input |

### Settings in `config.py` (Less Frequently Changed)

| Setting | Purpose | GUI Control |
|---------|---------|-------------|
| `ACTIVE_SCHEMA` | Naming convention selector | Dropdown |
| `VALUE_MAPPINGS` | Number-to-name translations | Table editor |
| `COMPARISON_CONFIGS` | Version comparison pairs | Dynamic list builder |
| `DATA_MANIPULATIONS` | Derived data operations | Advanced panel |

---

## Phase 2: GUI Layout

### Recommended Framework
- **Tkinter** (built-in, no dependencies)
- **PyQt/PySide** (more polished, requires install)

### Main Window Sections

```
┌─────────────────────────────────────────────────────────────┐
│  CFD Data Processing                              [Run ▶]   │
├─────────────────────────────────────────────────────────────┤
│  ┌─ Data Sources ─────────────────────────────────────────┐ │
│  │ [+ Add Folder]  [- Remove]                             │ │
│  │ ┌─────────────────────────────────────────────────────┐│ │
│  │ │ C:\...\2414_006_004.3\4.3.1.2                       ││ │
│  │ │ C:\...\2414_006_004.3\4.3.2.1                       ││ │
│  │ │ C:\...\2414_006_004.3\4.3.3.1                       ││ │
│  │ └─────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  Output Directory: [________________________] [Browse...]   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─ Processing Options ───────────────────────────────────┐ │
│  │ Comparison Mode:    [turbulence    ▼]                  │ │
│  │ Extraction Method:  [case_file     ▼]                  │ │
│  │ Naming Schema:      [4-part        ▼]                  │ │
│  │ Iterations for Stats: [150    ]                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Convergence Analysis ─────────────────────────────────┐ │
│  │ [✓] Enable Convergence Analysis                        │ │
│  │     Max Trim: [====●=====] 80%                         │ │
│  │     Tests:    [20    ]                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Physics Parameters ───────────────────────────────────┐ │
│  │ Span (m):        [0.85344 ]   Chord (m):    [0.1    ]  │ │
│  │ Air Density:     [1.225   ]   Velocity:     [24.38  ]  │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─ Console Output ───────────────────────────────────────┐ │
│  │ Loading data from 3 sources...                         │ │
│  │ ✓ Loaded 24 configuration-AoA combinations             │ │
│  │ ...                                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 3: Code Changes Required

### 1. Create Config Loader (`config_loader.py`)

```python
import yaml
from pathlib import Path

def load_config(config_path: str = "run_config.yaml") -> dict:
    """Load and validate runtime configuration."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Convert string paths to Path objects
    config["data_sources"] = [Path(p) for p in config["data_sources"]]
    config["output_dir"] = Path(config["output_dir"])
    
    # Calculate derived values
    physics = config["physics"]
    physics["reference_area"] = physics["span"] * physics["chord"]
    physics["dynamic_pressure"] = 0.5 * physics["air_density"] * physics["velocity"]**2
    physics["q_times_a"] = physics["dynamic_pressure"] * physics["reference_area"]
    
    return config

def save_config(config: dict, config_path: str = "run_config.yaml"):
    """Save configuration to YAML file."""
    # Convert Path objects to strings for YAML
    output = config.copy()
    output["data_sources"] = [str(p) for p in config["data_sources"]]
    output["output_dir"] = str(config["output_dir"])
    
    with open(config_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False)
```

### 2. Modify `main.py`

```python
# Replace hardcoded config with:
from config_loader import load_config

def main(config_path: str = "run_config.yaml"):
    config = load_config(config_path)
    
    DATA_SOURCES = config["data_sources"]
    OUTPUT_DIR = config["output_dir"]
    # ... etc
```

### 3. GUI App (`gui.py`)

The GUI would:
1. Load existing `run_config.yaml` on startup
2. Populate all fields with current values
3. On "Run" button: save config → call `main()`
4. Capture stdout to display in console panel

---

## Validation Requirements

Before running, the GUI should validate:

- [ ] At least one data source path exists
- [ ] Output directory is writable
- [ ] Physics values are positive numbers
- [ ] `NUM_ITERATIONS` > 0
- [ ] `CONVERGENCE_MAX_TRIM` between 0.0 and 1.0

---

## Future Enhancements

1. **Preset Profiles** - Save/load named configurations
2. **Progress Bar** - Show processing progress instead of console
3. **Results Viewer** - Display generated Excel/graphs inline
4. **Batch Mode** - Queue multiple configs to run sequentially
5. **Dark Mode** - Toggle light/dark theme

---

## Dependencies to Add

```bash
pip install pyyaml  # For config file support
# Tkinter is built-in, no install needed
# OR for PyQt:
pip install PyQt6
```
