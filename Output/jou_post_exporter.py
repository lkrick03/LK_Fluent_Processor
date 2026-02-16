"""
ANSYS Fluent Post-Processing Journal Exporter
==============================================
Generate journal files (.jou) to batch-load completed simulations
and export Cp and Y+ XY data from airfoil surfaces.

Usage:
    1. Configure the settings in the CONFIGURATION section below
    2. Run the script: python jou_post_exporter.py
    3. Open the generated .jou file in ANSYS Fluent
"""

import os
from datetime import datetime

# ============================================================
# CONFIGURATION - MODIFY THIS SECTION
# ============================================================

# OUTPUT SETTINGS — where the .jou file itself is saved
export_filename = "post_process_4.6.1.1.NG"          # Filename (no .jou needed)
export_directory = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414.6.4.6\4.6.1.1.NG"

# --- 1. Case/Data File Locations ---
# Base directory containing AoA_<angle> folders with case/data files
BASE_CASE_DIR = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414.6.4.6\4.6.1.1.NG"

# Configuration name (matches your file naming convention, e.g. "4.6.1.1.NG")
CONFIG_NAME = "4.6.1.1.NG"

# List of AoA values to process
AOA_LIST = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]

# --- 2. XY Data Output Directory ---
# Set to None to save exported .xy files alongside each case file
# Or set a path to collect all exports in one place
# Keep the folder name y_plus_pressure_data, otherwise main.py needs to be changed
XY_OUTPUT_DIR = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414.6.4.6\4.6.1.1.NG\y_plus_pressure_data"

# --- 3. Airfoil Wall Surface Names ---
# Instance numbers that make up the airfoil wall
AIRFOIL_WALL_INSTANCES = [1, 2, 3, 20, 21, 22, 23, 24, 32, 33, 34, 35, 36]
AIRFOIL_SURFACE_TEMPLATE = "wall-enclosure-enclosure_instance_{}_solid1"

# --- 4. Variables to Export ---
# Format: { "fluent-variable-name": "output-label" }
# Available Fluent variables for /plot/plot:
#   abs-angular-coordinate, absolute-pressure, angular-coordinate, anisotropic-adaption-cells,
#   aspect-ratio, axial-coordinate, axial-velocity, boundary-cell-dist, boundary-layer-cells,
#   boundary-normal-dist, boundary-volume-dist, cell-element-type, cell-equiangle-skew,
#   cell-equivolume-skew, cell-id, cell-parent-index, cell-partition-active, cell-partition-stored,
#   cell-refine-level, cell-reynolds-number, cell-type, cell-volume, cell-volume-change,
#   cell-wall-distance, cell-weight, cell-zone, density, density-all, dp-dx, dp-dy, dp-dz,
#   dx-velocity-dx, dx-velocity-dy, dx-velocity-dz, dy-velocity-dx, dy-velocity-dy, dy-velocity-dz,
#   dynamic-pressure, dz-velocity-dx, dz-velocity-dy, dz-velocity-dz, face-area-magnitude,
#   face-handedness, helicity, interface-overlap-fraction, lambda2-criterion, mark-poor-elements,
#   mass-imbalance, mesh-x-velocity, mesh-y-velocity, mesh-z-velocity, orthogonal-quality,
#   partition-neighbors, pressure, pressure-coefficient, pressure-hessian-indicator, production-of-k,
#   q-criterion, radial-coordinate, radial-velocity, raw-q-criterion, rel-axial-velocity,
#   rel-radial-velocity, rel-tangential-velocity, rel-total-pressure, rel-velocity-magnitude,
#   relative-velocity-angle, relative-x-velocity, relative-y-velocity, relative-z-velocity,
#   skin-friction-coef, smoothed-cell-refine-level, specific-diss-rate, strain-rate-mag,
#   tangential-velocity, total-pressure, turb-diss-rate, turb-intensity, turb-kinetic-energy,
#   turb-reynolds-number-rey, velocity-angle, velocity-magnitude, viscosity-eff, viscosity-lam,
#   viscosity-ratio, viscosity-turb, vorticity-mag, wall-shear, wall-temp-in-surf, wall-temp-out-surf,
#   x-coordinate, x-face-area, x-velocity, x-vorticity, x-wall-shear, y-coordinate, y-face-area,
#   y-plus, y-star, y-velocity, y-vorticity, y-wall-shear, z-coordinate, z-face-area, z-velocity,
#   z-vorticity, z-wall-shear
EXPORT_VARIABLES = {
    "pressure-coefficient": "Cp",
    "yplus": "Yplus",
    "skin-friction-coef": "Skin_Friction",
}

# --- 5. Plot Settings ---
# Direction vector for the X-axis of the XY plot (position along chord)
# Use "1 0" for 2D solvers, "1 0 0" for 3D solvers
PLOT_DIRECTION = "1 0 0"


# ============================================================
# SCRIPT LOGIC — NO NEED TO MODIFY BELOW
# ============================================================

def get_airfoil_surfaces():
    """Build the list of airfoil wall surface names from instance numbers."""
    return [AIRFOIL_SURFACE_TEMPLATE.format(i) for i in AIRFOIL_WALL_INSTANCES]


def to_fluent_path(windows_path):
    """Convert a Windows path to forward-slash format for Fluent journal files."""
    return windows_path.replace("\\", "/")


def generate_journal_content():
    """Generate the ANSYS Fluent post-processing journal file content."""

    surfaces = get_airfoil_surfaces()
    surface_tui_string = " ".join(surfaces)

    # Build list of case info
    cases = []
    for aoa in AOA_LIST:
        aoa_str = str(aoa) if isinstance(aoa, int) else f"{aoa}"
        case_dir = os.path.join(BASE_CASE_DIR, f"AoA_{aoa_str}")
        case_file = os.path.join(case_dir, f"{CONFIG_NAME}.{aoa_str}.cas.h5")
        cases.append({
            "aoa": aoa,
            "aoa_str": aoa_str,
            "case_file": to_fluent_path(case_file),
            "case_dir": to_fluent_path(case_dir),
        })

    # Determine output dir (Fluent-compatible path)
    if XY_OUTPUT_DIR:
        output_base = to_fluent_path(XY_OUTPUT_DIR)
    else:
        output_base = None  # will use per-case directory

    # --- Build Journal Header ---
    journal = f"""; ============================================================
; ANSYS Fluent Post-Processing Journal — Auto-Generated
; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; Config:    {CONFIG_NAME}
; AoA List:  {AOA_LIST}
; Variables: {', '.join(EXPORT_VARIABLES.values())}
; ============================================================

"""

    # --- Create output directory if specified ---
    if output_base:
        journal += f'; Create output directory\n'
        journal += f'(system "mkdir \\"{output_base}\\"")\n\n'

    # --- Loop through each AoA ---
    for case in cases:
        aoa = case["aoa"]
        aoa_str = case["aoa_str"]
        out_dir = output_base if output_base else case["case_dir"]

        journal += f"""; ------------------------------------------------------------
; Post-Processing AoA = {aoa}
; ------------------------------------------------------------
(display (format #f "~%===== Loading AoA = {aoa} =====~%"))

; Load case and data
(ti-menu-load-string "/file/read-case-data \\"{case['case_file']}\\"")

"""

        # Export each variable
        for var_name, label in EXPORT_VARIABLES.items():
            output_file = f"{out_dir}/{CONFIG_NAME}.{aoa_str}.{label}.xy"

            journal += f"""; Export {label}
(display "  Exporting {label} for AoA = {aoa}...\\n")
(ti-menu-load-string "/plot/plot yes \\"{output_file}\\" no no no {var_name} yes {PLOT_DIRECTION} {surface_tui_string} ()")

"""

    # --- Footer ---
    journal += '(display (format #f "~%=== Post-processing completed successfully ===~%"))\\n'

    return journal, len(cases)


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
    """Main function to generate and export the post-processing journal."""
    print("=" * 70)
    print("ANSYS Fluent Post-Processing Journal Exporter")
    print("=" * 70)

    # Generate journal content
    journal_content, num_cases = generate_journal_content()
    surfaces = get_airfoil_surfaces()

    print(f"  Config:     {CONFIG_NAME}")
    print(f"  AoA Steps:  {num_cases}")
    print(f"  Surfaces:   {len(surfaces)} airfoil wall zones")
    print(f"  Variables:  {', '.join(EXPORT_VARIABLES.values())}")

    if XY_OUTPUT_DIR:
        print(f"  XY Output:  {XY_OUTPUT_DIR}")
    else:
        print(f"  XY Output:  Saved alongside each case file")

    # Export the journal
    print("\nExporting journal file...")
    filepath = export_journal(export_filename, journal_content, export_directory)

    file_size = os.path.getsize(filepath)
    print(f"\n[OK] Journal file exported successfully!")
    print(f"  Filename:  {os.path.basename(filepath)}")
    print(f"  Location:  {filepath}")
    print(f"  Size:      {file_size} bytes")
    print(f"\nNext steps:")
    print(f"  1. Open ANSYS Fluent")
    print(f"  2. File > Read > Journal  (or /file/read-journal in the console)")
    print(f"  3. Select: {os.path.basename(filepath)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
