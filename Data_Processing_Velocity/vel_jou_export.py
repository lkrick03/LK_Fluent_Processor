"""
ANSYS Journal File Exporter (Mach Sweep)
========================================
Generate and export ANSYS Fluent journal files (.jou) for Mach sweep simulations.

* NOTE: This script has been merged with `jou_post_exporter.py`! 
* It now natively handles solving AND post-processing. You DO NOT 
* need to run a secondary post-exporter script. It automatically 
* generates .xy and pathline data arrays straight into the Mach folders.

Usage:
    1. Configure the settings in the CONFIGURATION section below
    2. Run the script: python vel_jou_export.py
    3. The .jou file will be saved to the specified export directory
"""

import os
import numpy as np
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION - MODIFY THIS SECTION
# ============================================================

# OUTPUT SETTINGS
export_filename = "1.2.1.7  .NG_0.05_0.8" # Filename (no .jou needed)
export_directory = r"C:\Users\lukek\OneDrive\Documents\Rocketry_ANSYS\OMEGA\Fluent\Setup_Jou\HPC\1.2.1.7.NG_setup"

# --- 1. Mach Settings ---
MACH_MODE = "List"  # Options: "Range", "List", "MultiRange"

# If "Range":
MACH_START = 0.05 
MACH_END = 0.8
MACH_STEP = 0.05

# If "MultiRange":
# List of tuples: (start, end, step)
MACH_RANGES = [
    (0.5, 1.5, 0.25),    # 0.5 to 1.5 with step 0.25
    (2.0, 3.0, 0.5)      # 2.0 to 3.0 with step 0.5
]

# If "List":
MACH_LIST = [0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8]

# --- 2. Simulation Parameters ---
X_FLOW_DIR = 0.0       # X-Component of Flow Direction
Y_FLOW_DIR = -1.0        # Y-Component of Flow Direction
Z_FLOW_DIR = 0.0        # Z-Component of Flow Direction
GAUGE_PRESSURE = 98900  # Gauge Pressure (Pa)
TEMPERATURE = 300       # Temperature (K)
TURB_INTENSITY = 5      # Turbulent Intensity (%)
TURB_VISCOSITY = 10     # Turbulent Viscosity Ratio
BASE_OUTPUT_DIR = "/home/ljcrick/directories/OMEGA/1.2.1.7.NG" 
OUTPUT_FILENAME_BASE = "1.2.1.7.NG"  # Base name for output files
DRAG_REPORT_FILE = "report-file-0" #make sure the report definiton has an output file and is named accordingly
ITERATIONS = 2400  # Number of iterations to run
TEST_MODE = False   # If True: Updates BCs but skips Solving & Saving

# --- 3. Define Zone Groups ---
GROUP_INLET_MAIN = [
    "farfield"
]

GROUP_SYMMETRY = [
    "symmetry"
]

# --- 4. Zone Logic Configuration ---
DEFAULT_ZONES = {
    "inlets":   GROUP_INLET_MAIN,
    "symmetry": GROUP_SYMMETRY
}

# Override rules for specific Mach numbers (if needed, kept for symmetry with AoA script)
ZONE_RULES = [
    # Example logic if certain Mach numbers required different BCs
    # {
    #     "mach_range": [0.5, 1.5],  # Start, End (Inclusive)
    #     "inlets": GROUP_INLET_MAIN,
    #     "outlets": GROUP_OUTLET_MAIN + GROUP_OUTLET_TOP + GROUP_INLET_BOTTOM,
    #     "symmetry": GROUP_SYMMETRY
    # }
]

# --- 5. Post-Processing Settings ---
# Rocket Wall Surfaces
ROCKET_SURFACES = ["fin_wall", "rocketbody_wall"]

# Format: { "fluent-variable-name": "output-label" }
EXPORT_VARIABLES = {
    "pressure-coefficient": "Cp",
    "yplus": "Yplus",
    "skin-friction-coef": "Skin_Friction",
}
PLOT_DIRECTION = "1 0 0"

EXPORT_RESIDUALS = True

# TUI Command Strings
# NOTE: The ~a wildcards will be replaced by: Mach Number, X-Dir, Y-Dir, Z-Dir
# The sequence answers:
# Profile/Pressure? -> no, GAUGE_PRESSURE
# Profile/Mach?     -> no, ~a
# Profile/Temp?     -> no, TEMPERATURE
# Cartesian?        -> yes
# Profile/X-Dir     -> no, ~a
# Profile/Y-Dir     -> no, ~a
# Profile/Z-Dir     -> no, ~a
# K/Omega?          -> no
# Intensity/Length? -> no
# Intensity/Visc?   -> yes, TURB_INTENSITY, TURB_VISCOSITY
INLET_TUI_SETTINGS = f"no {GAUGE_PRESSURE} no ~a no {TEMPERATURE} yes no ~a no ~a no ~a no no yes {TURB_INTENSITY} {TURB_VISCOSITY}"
OUTLET_TUI_SETTINGS = "yes no 0 no yes no no yes 5 10 yes no no no"

def format_scheme_list(py_list):
    """Format a Python list as a Scheme list."""
    if not py_list:
        return "'()"
    quoted_items = [f'"{item}"' for item in py_list]
    return f"'({' '.join(quoted_items)})"


def get_rocket_surfaces():
    return ROCKET_SURFACES

def _build_residual_scheme_for_velocity(res_file, mach):
    names_list = (
        '"continuity" "x-velocity" "y-velocity" "z-velocity" '
        '"energy" "k" "omega" "epsilon" "nut"'
    )

    scheme = f"""; --- Residual Export (Scheme) for Mach = {mach} ---
(display "  Exporting residuals for Mach = {mach}...\\n")
(let ((port (open-output-file "{res_file}"))
      (iters (residual-history "iteration"))
      (names '())
      (datas '()))
  (for-each
    (lambda (name)
      (let ((d (residual-history name)))
        (if (and (pair? d) (> (length d) 0))
          (begin
            (set! names (append names (list name)))
            (set! datas (append datas (list d)))))))
    (list {names_list}))
  (display "iteration" port)
  (for-each (lambda (nm) (display "\\t" port) (display nm port)) names)
  (newline port)
  (let ((n (length iters)))
    (do ((i 0 (+ i 1)))
        ((>= i n))
      (display (list-ref iters i) port)
      (for-each (lambda (d) (display "\\t" port) (display (list-ref d i) port)) datas)
      (newline port)))
  (close-output-port port)
  (display (format #f "    Wrote ~a iterations x ~a residuals to file\\n" (length iters) (length names))))

"""
    return scheme

def generate_journal_content():
    """Generate the ANSYS Fluent journal file content."""
    
    # Determine Mach sequence
    if MACH_MODE == "Range":
        mach_values = list(np.arange(MACH_START, MACH_END + 0.0001, MACH_STEP))
        config_note = f"Range: {MACH_START} to {MACH_END} step {MACH_STEP}"
    elif MACH_MODE == "MultiRange":
        val_list = []
        for r_start, r_end, r_step in MACH_RANGES:
            # Generate range, round to 4 decimals to avoid float duplication
            vals = np.arange(r_start, r_end + 0.0001, r_step)
            val_list.extend([round(v, 4) for v in vals])
        
        # Remove duplicates and sort
        mach_values = sorted(list(set(val_list)))
        config_note = f"MultiRange: {MACH_RANGES}"
    else:
        mach_values = MACH_LIST
        config_note = f"List: {MACH_LIST}"

    # Build journal header
    journal_content = f"""; ============================================================
; ANSYS Fluent Journal File — Auto-Generated
; Config: {config_note}
; Const Flow Direction: [X: {X_FLOW_DIR}, Y: {Y_FLOW_DIR}, Z: {Z_FLOW_DIR}]
; Test Mode: {TEST_MODE}
; ============================================================

(define base-output-dir "{BASE_OUTPUT_DIR}")

(define drag-report-file-name "{DRAG_REPORT_FILE}")

(define (ensure-directory dir-path)
  (system (format #f "mkdir -p \\"~a\\"" dir-path)))

; Create base directory
(ensure-directory base-output-dir)
"""

    # Prepare post-processing constants
    surfaces = get_rocket_surfaces()
    surface_tui_string = " ".join(surfaces)

    # Iterate through each Mach number
    for mach in mach_values:
        # Start with defaults
        target_inlets = DEFAULT_ZONES.get("inlets", [])
        target_outlets = DEFAULT_ZONES.get("outlets", [])
        target_symmetry = DEFAULT_ZONES.get("symmetry", [])

        # Apply override rules
        for rule in ZONE_RULES:
            is_match = False
            
            if "mach_list" in rule:
                if mach in rule["mach_list"]:
                    is_match = True
            
            if not is_match and "mach_range" in rule:
                r_start, r_end = rule["mach_range"]
                if r_start <= mach <= r_end:
                    is_match = True
            
            if is_match:
                if "inlets" in rule:
                    target_inlets = rule["inlets"]
                if "outlets" in rule:
                    target_outlets = rule["outlets"]
                if "symmetry" in rule:
                    target_symmetry = rule["symmetry"]

        # Convert to Scheme strings
        s_inlets = format_scheme_list(target_inlets)
        s_outlets = format_scheme_list(target_outlets)
        s_symmetries = format_scheme_list(target_symmetry)

        # Handle Test Mode
        if TEST_MODE:
            solve_block = '; [TEST MODE] Solver skipped'
            save_block = '; [TEST MODE] Save skipped'
            iter_display = f'(display "  [TEST] Applying BCs for Mach {mach}, skipping solve/save...\\n")'
        else:
            solve_block = f'(ti-menu-load-string "/solve/iterate {ITERATIONS}")'
            save_block = '(ti-menu-load-string (format #f "/file/write-case-data ~a/~a yes" current-mach-dir case-data-name))'
            iter_display = f'(display "Running {ITERATIONS} iterations for Mach {mach}...\\n")'

        journal_content += f"""
; ------------------------------------------------------------
; Running Mach = {mach}
; ------------------------------------------------------------
(define mach-number {mach})
(define current-mach-dir (format #f "~a/Mach_~a" base-output-dir mach-number))
(ensure-directory current-mach-dir)

(display (format #f "~%===== Running Mach = ~a =====~%" mach-number))

; Set Flow Directions for Pressure Far-Field
(define dir_x {X_FLOW_DIR})
(define dir_y {Y_FLOW_DIR})
(define dir_z {Z_FLOW_DIR})

; Update Report Files
(define new-drag-path (format #f "~a/drag_force_Mach_~a.txt" current-mach-dir mach-number))

(ti-menu-load-string (format #f "/solve/report-files/edit ~a file-name \\"~a\\" q" drag-report-file-name new-drag-path))

; Apply Boundary Conditions
(define inlet-list {s_inlets})
(define outlet-list {s_outlets})
(define symmetry-list {s_symmetries})

; Inlets
(if (not (null? inlet-list))
  (for-each
    (lambda (zone)
      ; FORCE ZONE TYPE TO PRESSURE-FAR-FIELD FIRST
      (ti-menu-load-string (format #f "/define/boundary-conditions/zone-type ~a pressure-far-field" zone))
      
      ; Now apply settings
      (ti-menu-load-string
        (format #f "/define/boundary-conditions/pressure-far-field ~a {INLET_TUI_SETTINGS}" zone mach-number dir_x dir_y dir_z)))
    inlet-list))

; Outlets
(if (not (null? outlet-list))
  (for-each
    (lambda (zone)
        (ti-menu-load-string (format #f "/define/boundary-conditions/zone-type ~a pressure-outlet" zone))
        (ti-menu-load-string (format #f "/define/boundary-conditions/pressure-outlet ~a {OUTLET_TUI_SETTINGS}" zone)))
    outlet-list))

; Symmetry
(if (not (null? symmetry-list))
  (for-each
    (lambda (zone)
        (ti-menu-load-string (format #f "/define/boundary-conditions/zone-type ~a symmetry" zone)))
    symmetry-list))

; Solve
{iter_display}
{solve_block}

; Save
(define case-data-name (format #f "{OUTPUT_FILENAME_BASE}.~a.cas.h5" mach-number))
{save_block}
"""

        # --- POST PROCESSING ---
        if not TEST_MODE:
            post_block = f"""
; Ensure post-process dir exists
(ensure-directory (format #f "~a/y_plus_pressure_data" current-mach-dir))
"""
            for var_name, label in EXPORT_VARIABLES.items():
                output_file = f"{BASE_OUTPUT_DIR}/Mach_{mach}/y_plus_pressure_data/{OUTPUT_FILENAME_BASE}.{mach}.{label}.xy"
                output_file = output_file.replace("\\", "/")
                
                post_block += f"""; Export {label}
(display "  Exporting {label} for Mach = {mach}...\\n")
(ti-menu-load-string (format #f "/plot/plot yes \\"{output_file}\\" no no no {var_name} yes {PLOT_DIRECTION} {surface_tui_string} ()"))

"""
            if EXPORT_RESIDUALS:
                res_file = f"{BASE_OUTPUT_DIR}/Mach_{mach}/y_plus_pressure_data/{OUTPUT_FILENAME_BASE}.{mach}.residuals.csv"
                res_file = res_file.replace("\\", "/")
                post_block += _build_residual_scheme_for_velocity(res_file, mach)
                
            journal_content += post_block

    journal_content += '\n(display "~%=== Mach sweep completed successfully ===~%")\n'
    
    return journal_content, len(mach_values)


def export_journal(filename, content, directory):
    """Export journal content to a .jou file."""
    os.makedirs(directory, exist_ok=True)
    
    if not filename.lower().endswith('.jou'):
        filename = filename + '.jou'
    
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def main():
    """Main function to generate and export the journal file."""
    print("=" * 70)
    print("ANSYS Journal File Exporter (Mach Sweep)")
    print("=" * 70)
    
    # Generate journal content
    journal_content, num_mach = generate_journal_content()
    print(f"[OK] Journal content generated for {num_mach} Mach steps")
    
    if TEST_MODE:
        print("[!] TEST MODE: Solving and saving disabled.")
    
    # Export the journal
    print("\nExporting journal file...")
    filepath = export_journal(export_filename, journal_content, export_directory)
    
    file_size = os.path.getsize(filepath)
    print(f"\n[OK] Journal file exported successfully!")
    print(f"  Filename: {os.path.basename(filepath)}")
    print(f"  Location: {filepath}")
    print(f"  Size: {file_size} bytes")
    print(f"\n[OK] Ready to use in ANSYS Fluent!")
    print("=" * 70)


if __name__ == "__main__":
    main()
