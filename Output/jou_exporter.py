"""
ANSYS Journal File Exporter
===========================
Generate and export ANSYS Fluent journal files (.jou) for AoA sweep simulations.

Usage:
    1. Configure the settings in the CONFIGURATION section below
    2. Run the script: python jou_exporter.py
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
export_filename = "4.6.1.2.NG.15_20"  # Filename (no .jou needed)
export_directory = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Data_Prepartation\HPC\4.6.1.2.NG_setup"

# --- 1. Angle of Attack (AoA) Settings ---
AOA_MODE = "List"  # Options: "Range", "List", "MultiRange"

# If "Range":
AOA_START = 0
AOA_END = 10
AOA_STEP = 1.0

# If "MultiRange":
# List of tuples: (start, end, step)
AOA_RANGES = [
    (5, 10, 0.5),    # 5 to 10 with step 0.5
    (11, 20, 1)  # 11 to 20 with step 1
]

# If "List":
AOA_LIST = [15, 16, 17, 18, 19, 20]

# --- 2. Simulation Parameters ---
V_MAG = 24.38      # Velocity magnitude (m/s)
BASE_OUTPUT_DIR = "/home/ljcrick/directories/4.6.1.2.NG"
OUTPUT_FILENAME_BASE = "4.6.1.2.NG"  # Base name for output files
DRAG_REPORT_FILE = "drag-rfile"
LIFT_REPORT_FILE = "lift-rfile"
ITERATIONS = 4000  # Number of iterations to run
TEST_MODE = False   # If True: Updates BCs but skips Solving & Saving

# --- 3. Define Zone Groups ---
GROUP_INLET_MAIN = [
    "inlet-enclosure-enclosure_instance_29_solid1",
    "inlet-enclosure-enclosure_instance_28_solid1",
    "inlet-enclosure-enclosure_instance_47_solid1",
    "inlet-enclosure-enclosure_instance_26_solid1",
    "inlet-enclosure-enclosure_instance_38_solid1",
    "inlet-enclosure-enclosure_instance_12_solid1"
]

GROUP_INLET_BOTTOM = [
    "inlet_bottom-enclosure-enclosure_instance_10_solid1",
    "inlet_bottom-enclosure-enclosure_instance_11_solid1",
    "inlet_bottom-enclosure-enclosure_instance_12_solid1",
    "inlet_bottom-enclosure-enclosure_instance_4_solid1",
    "inlet_bottom-enclosure-enclosure_instance_5_solid1",
    "inlet_bottom-enclosure-enclosure_instance_6_solid1",
    "inlet_bottom-enclosure-enclosure_instance_7_solid1",
    "inlet_bottom-enclosure-enclosure_instance_8_solid1",
    "inlet_bottom-enclosure-enclosure_instance_9_solid1"
]

GROUP_OUTLET_MAIN = [
    "outlet-enclosure-enclosure_instance_18_solid1",
    "outlet-enclosure-enclosure_instance_27_solid1",
    "outlet-enclosure-enclosure_instance_30_solid1",
    "outlet-enclosure-enclosure_instance_39_solid1",
    "outlet-enclosure-enclosure_instance_4_solid1"
]

GROUP_OUTLET_TOP = [
    "outlet_top-enclosure-enclosure_instance_39_solid1",
    "outlet_top-enclosure-enclosure_instance_40_solid1",
    "outlet_top-enclosure-enclosure_instance_41_solid1",
    "outlet_top-enclosure-enclosure_instance_42_solid1",
    "outlet_top-enclosure-enclosure_instance_43_solid1",
    "outlet_top-enclosure-enclosure_instance_44_solid1",
    "outlet_top-enclosure-enclosure_instance_45_solid1",
    "outlet_top-enclosure-enclosure_instance_46_solid1",
    "outlet_top-enclosure-enclosure_instance_47_solid1"
]

GROUP_SYMMETRY = []

# --- 4. Zone Logic Configuration ---
DEFAULT_ZONES = {
    "inlets":   GROUP_INLET_MAIN + GROUP_INLET_BOTTOM,
    "outlets":  GROUP_OUTLET_MAIN + GROUP_OUTLET_TOP,
    "symmetry": GROUP_SYMMETRY
}

# Override rules for specific AoAs
ZONE_RULES = [
    {
        "aoa_range": [0, 4],  # Start, End (Inclusive)
        "inlets": GROUP_INLET_MAIN,
        "outlets": GROUP_OUTLET_MAIN + GROUP_OUTLET_TOP,
        "symmetry": GROUP_INLET_BOTTOM
    }
]

# TUI Command Strings
INLET_TUI_SETTINGS = "no yes yes no 0 yes no ~a no ~a no ~a no no yes 0.05 10"
OUTLET_TUI_SETTINGS = "yes no 0 no yes no no yes 5 10 yes no no no"

def format_scheme_list(py_list):
    """Format a Python list as a Scheme list."""
    if not py_list:
        return "'()"
    quoted_items = [f'"{item}"' for item in py_list]
    return f"'({' '.join(quoted_items)})"


def generate_journal_content():
    """Generate the ANSYS Fluent journal file content."""
    
    # Determine AoA sequence
    if AOA_MODE == "Range":
        aoa_values = list(np.arange(AOA_START, AOA_END + 0.0001, AOA_STEP))
        config_note = f"Range: {AOA_START} to {AOA_END} step {AOA_STEP}"
    elif AOA_MODE == "MultiRange":
        val_list = []
        for r_start, r_end, r_step in AOA_RANGES:
            # Generate range, round to 4 decimals to avoid float duplication
            vals = np.arange(r_start, r_end + 0.0001, r_step)
            val_list.extend([round(v, 4) for v in vals])
        
        # Remove duplicates and sort
        aoa_values = sorted(list(set(val_list)))
        config_note = f"MultiRange: {AOA_RANGES}"
    else:
        aoa_values = AOA_LIST
        config_note = f"List: {AOA_LIST}"

    # Build journal header
    journal_content = f"""; ============================================================
; ANSYS Fluent Journal File — Auto-Generated
; Config: {config_note}
; Velocity: {V_MAG} m/s
; Test Mode: {TEST_MODE}
; ============================================================

(define base-output-dir "{BASE_OUTPUT_DIR}")
(define V_mag {V_MAG})

(define drag-report-file-name "{DRAG_REPORT_FILE}")
(define lift-report-file-name "{LIFT_REPORT_FILE}")

(define (deg-to-rad deg) (* deg (/ 3.14159265359 180.0)))
(define (ensure-directory dir-path)
  (system (format #f "mkdir \\"~a\\"" dir-path)))

; Create base directory
(ensure-directory base-output-dir)
"""

    # Iterate through each AoA
    for aoa in aoa_values:
        # Start with defaults
        target_inlets = DEFAULT_ZONES["inlets"]
        target_outlets = DEFAULT_ZONES["outlets"]
        target_symmetry = DEFAULT_ZONES["symmetry"]

        # Apply override rules
        for rule in ZONE_RULES:
            is_match = False
            
            if "aoa_list" in rule:
                if aoa in rule["aoa_list"]:
                    is_match = True
            
            if not is_match and "aoa_range" in rule:
                r_start, r_end = rule["aoa_range"]
                if r_start <= aoa <= r_end:
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
            iter_display = f'(display "  [TEST] Applying BCs for AoA {aoa}, skipping solve/save...\\n")'
        else:
            solve_block = f'(ti-menu-load-string "/solve/iterate {ITERATIONS}")'
            save_block = '(ti-menu-load-string (format #f "/file/write-case-data ~a/~a yes" current-aoa-dir case-data-name))'
            iter_display = f'(display "Running {ITERATIONS} iterations for AoA {aoa}...\\n")'

        journal_content += f"""
; ------------------------------------------------------------
; Running AoA = {aoa}
; ------------------------------------------------------------
(define aoa {aoa})
(define current-aoa-dir (format #f "~a/AoA_~a" base-output-dir aoa))
(ensure-directory current-aoa-dir)

(display (format #f "~%===== Running AoA = ~a =====~%" aoa))

; Calculate Velocity Components
(define aoa_rad (deg-to-rad aoa))
(define V_x (* V_mag (cos aoa_rad)))
(define V_y (* V_mag (sin aoa_rad)))
(define V_z 0.0)

; Update Report Files
(define new-drag-path (format #f "~a/drag_force_AoA_~a.txt" current-aoa-dir aoa))
(define new-lift-path (format #f "~a/lift_force_AoA_~a.txt" current-aoa-dir aoa))

(ti-menu-load-string (format #f "/solve/report-files/edit ~a file-name \\"~a\\" q" drag-report-file-name new-drag-path))
(ti-menu-load-string (format #f "/solve/report-files/edit ~a file-name \\"~a\\" q" lift-report-file-name new-lift-path))

; Apply Boundary Conditions
(define inlet-list {s_inlets})
(define outlet-list {s_outlets})
(define symmetry-list {s_symmetries})

; Inlets
(if (not (null? inlet-list))
  (for-each
    (lambda (zone)
      ; FORCE ZONE TYPE TO VELOCITY-INLET FIRST
      (ti-menu-load-string (format #f "/define/boundary-conditions/zone-type ~a velocity-inlet" zone))
      
      ; Now apply settings
      (ti-menu-load-string
        (format #f "/define/boundary-conditions/velocity-inlet ~a {INLET_TUI_SETTINGS}" zone V_x V_y V_z)))
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
(define case-data-name (format #f "{OUTPUT_FILENAME_BASE}.~a.cas.h5" aoa))
{save_block}
"""

    journal_content += '\n(display "~%=== AoA sweep completed successfully ===~%")\n'
    
    return journal_content, len(aoa_values)


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
    print("ANSYS Journal File Exporter")
    print("=" * 70)
    
    # Generate journal content
    journal_content, num_aoa = generate_journal_content()
    print(f"[OK] Journal content generated for {num_aoa} AoA steps")
    
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
