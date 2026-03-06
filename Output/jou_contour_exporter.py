"""
ANSYS Fluent Post-Processing Journal Exporter for Contour Plots
===============================================================
Generate journal files (.jou) to batch-load completed simulations
and save contour plot images (e.g. PNG).

Usage:
    1. Configure the settings in the CONFIGURATION section below
    2. Run the script: python jou_contour_exporter.py
    3. Open the generated .jou file in ANSYS Fluent
"""

import os
import re
from datetime import datetime

# ============================================================
# CONFIGURATION - MODIFY THIS SECTION
# ============================================================

# OUTPUT SETTINGS — where the .jou file itself is saved
export_filename = "post_process_contours_5.6.1.1.NG"          # Filename (no .jou needed)
export_directory = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414.6.5.6\5.6.1.1.NG"

# --- 1. Base Locations & Naming ---
# The parent directory containing the AoA_* folders for this specific config
BASE_CASE_DIR = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414.6.5.6\5.6.1.1.NG"

# Configuration name (matches your file naming convention, e.g. "4.6.1.1.NG")
CONFIG_NAME = "5.6.1.1.NG"

# List of AoA values to process
# Leave empty [] to auto-discover all AoA_* folders (supports decimals like AoA_7.5)
AOA_LIST = [5,10]

# --- 2. Input/Output Paths ---
# Set to None to save images alongside each case file
# Or set a path to collect all exports in one place
IMAGE_OUTPUT_DIR = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.1.NG\Countour_Plots"

# Path to the saved Fluent Camera View file (.vw) used for exact image framing
# Ensure this file exists and contains the layouts referenced in Custom Views
CAMERA_VIEW_FILE = r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Views\Views_5.vw"

# --- 3. Airfoil Wall Surface Names ---
# Instance numbers that make up the airfoil wall
AIRFOIL_WALL_INSTANCES = [1, 2, 3, 20, 21, 22, 23, 24, 32, 33, 34, 35, 36]
AIRFOIL_SURFACE_TEMPLATE = "wall-enclosure-enclosure_instance_{}_solid1"

# Provide a space-separated list of any *additional* surface names if you want to plot on them
ADDITIONAL_CONTOUR_SURFACES = "custom_plane"

# --- 3.5. Auto-Create Plane Surface ---
# Set to True if you want the script to generate a 2D cut-plane through your 3D domain
CREATE_PLANE_SURFACE = True
# Name of the plane to be created (must match one of the names in CONTOUR_SURFACES above)
PLANE_NAME = "custom_plane"
# Origin point of the plane (x y z)
PLANE_ORIGIN = "0 0 0"
# Normal vector of the plane (e.g. "0 0 1" for a Z-normal symmetry plane)
PLANE_NORMAL = "0 0 1"

# --- 4. Variables to Plot as Contours ---
# Format: { "fluent-variable-name": "output-label" }
CONTOUR_VARIABLES = {
    "pressure": "Static_Pressure",
    "pressure-coefficient": "Cp_Contour",
    "velocity-magnitude": "Velocity_Magnitude",
    "skin-friction-coef": "Skin_Friction",
}

# --- 5. Image Format Settings ---
IMAGE_DRIVER = "png"      # Options: png, jpeg, tiff
RESOLUTION_X = 1920
RESOLUTION_Y = 1080

# --- 6. Rotation Settings ---
# Set to True if you want the camera to rotate by the Angle of Attack
ROTATE_IMAGE_TO_AOA = True
# Try 1.0 or -1.0 depending on the rotation direction you want in Fluent
ROTATE_ANGLE_MULTIPLIER = -1.0

# --- 7. Custom Views per Variable (Optional) ---
# If you want specific variables to be viewed from a different angle or zoom level
# before they are saved, you can add TUI commands here.
# Leave the string empty "" if you want no special view changes.
# Note: You can stack commands by separating them with a newline \n
fluent_camera_path = CAMERA_VIEW_FILE.replace("\\", "/")

CUSTOM_VIEWS = {
    "pressure": "airfoil_center",
    "velocity-magnitude": "airfoil_center",
    "skin-friction-coef": "airfoil_surface",
}

# ============================================================
# SCRIPT LOGIC — NO NEED TO MODIFY BELOW
# ============================================================

def discover_aoa_folders(base_dir):
    """Auto-discover AoA values from AoA_* folders in base_dir."""
    aoa_values = []
    aoa_pattern = re.compile(r'^AoA_(-?\d+\.?\d*)$')
    
    if not os.path.isdir(base_dir):
        print(f"  [WARNING] Base directory not found: {base_dir}")
        return aoa_values
    
    for entry in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, entry)):
            match = aoa_pattern.match(entry)
            if match:
                val = float(match.group(1))
                if val == int(val):
                    val = int(val)
                aoa_values.append(val)
    
    aoa_values.sort(key=lambda x: float(x))
    return aoa_values


def get_airfoil_surfaces():
    """Build the list of airfoil wall surface names from instance numbers."""
    return [AIRFOIL_SURFACE_TEMPLATE.format(i) for i in AIRFOIL_WALL_INSTANCES]


def to_fluent_path(windows_path):
    """Convert a Windows path to forward-slash format for Fluent journal files."""
    return windows_path.replace("\\", "/")


def generate_journal_content():
    """Generate the ANSYS Fluent contour post-processing journal file content."""

    # Build the combined string of surfaces to plot on
    surfaces = get_airfoil_surfaces()
    airfoil_tui_string = " ".join(surfaces)
    surface_tui_string = airfoil_tui_string
    if ADDITIONAL_CONTOUR_SURFACES:
        surface_tui_string += f" {ADDITIONAL_CONTOUR_SURFACES}"

    # Determine AoA list: use configured list, or auto-discover if empty
    aoa_list = AOA_LIST
    if not aoa_list:
        print("  AOA_LIST is empty — auto-discovering AoA folders...")
        aoa_list = discover_aoa_folders(BASE_CASE_DIR)
        if not aoa_list:
            print("  [ERROR] No AoA_* folders found in BASE_CASE_DIR!")
            return "", 0
        print(f"  Found {len(aoa_list)} AoA values: {aoa_list}")

    # Build list of case info
    cases = []
    for aoa in aoa_list:
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
    if IMAGE_OUTPUT_DIR:
        output_base = to_fluent_path(IMAGE_OUTPUT_DIR)
    else:
        output_base = None

    # --- Build Journal Header ---
    journal = f"""; ============================================================
; ANSYS Fluent Contour Post-Processing Journal — Auto-Generated
; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; Config:    {CONFIG_NAME}
; AoA List:  {AOA_LIST}
; Variables: {', '.join(CONTOUR_VARIABLES.values())}
; ============================================================

; Set up display settings for saving high-quality images
(ti-menu-load-string "/display/set/picture/driver {IMAGE_DRIVER}")
(ti-menu-load-string "/display/set/picture/x-resolution {RESOLUTION_X}")
(ti-menu-load-string "/display/set/picture/y-resolution {RESOLUTION_Y}")
(ti-menu-load-string "/display/set/picture/color-mode color")
(ti-menu-load-string "/display/set/contours/filled-contours yes")
(ti-menu-load-string "/display/views/read-views \\"{fluent_camera_path}\\"")

"""

    # --- Create output directory if specified ---
    if output_base:
        os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

    # --- Loop through each AoA ---
    for case in cases:
        aoa = case["aoa"]
        aoa_str = case["aoa_str"]
        base_out = output_base if output_base else case["case_dir"]
        out_dir = f"{base_out}/AoA_{aoa_str}"

        # Create directory using Python instead of Fluent TUI
        os.makedirs(os.path.normpath(out_dir), exist_ok=True)

        journal += f"""; ------------------------------------------------------------
; Post-Processing AoA = {aoa}
; ------------------------------------------------------------
(display (format #f "~%===== Loading AoA = {aoa} =====~%"))

; Load case and data
(ti-menu-load-string "/file/read-case-data \\"{case['case_file']}\\"")

"""

        if CREATE_PLANE_SURFACE:
            journal += f"""; Create custom cross-sectional plane for 3D visualization
(ti-menu-load-string "/surface/plane-point-n-normal {PLANE_NAME} {PLANE_ORIGIN} {PLANE_NORMAL}")

"""

        # Export each variable as a contour plot
        for var_name, label in CONTOUR_VARIABLES.items():
            output_file = f"{out_dir}/{CONFIG_NAME}.{aoa_str}.{label}.{IMAGE_DRIVER}"

            # Only plot Skin Friction on actual physical walls, not mathematical cut planes
            current_surfaces = airfoil_tui_string if var_name == "skin-friction-coef" else surface_tui_string

            journal += f"""; Save Contour Plot for {label}
(display "  Exporting {label} contour for AoA = {aoa}...\\n")
(ti-menu-load-string "/display/set/contours/surfaces {current_surfaces} ()")
(ti-menu-load-string "/display/set/contours/node-values? yes")
"""

            # Draw the contour *before* the camera view is restored
            journal += f"""(ti-menu-load-string "/display/contour {var_name} , ,")
"""

            # Apply any custom views (like side views or zooms) for this specific variable
            if var_name in CUSTOM_VIEWS and CUSTOM_VIEWS[var_name]:
                view_name = CUSTOM_VIEWS[var_name]
                journal += f"""; Apply custom view/zoom
(ti-menu-load-string "/display/views/restore-view {view_name}")

"""
            # Rotate camera AFTER restoring the view so the rotation is not wiped out
            if ROTATE_IMAGE_TO_AOA and float(aoa) != 0.0:
                roll_angle = float(aoa) * ROTATE_ANGLE_MULTIPLIER
                journal += f"""; Rotate camera so the airfoil remains horizontal
(ti-menu-load-string "/display/views/camera/roll-camera {roll_angle}")

"""

            journal += f"""(ti-menu-load-string "/display/save-picture \\"{output_file}\\"")

"""

    # --- Footer ---
    journal += '(display (format #f "~%=== Post-processing completed successfully ===~%"))\n'

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
    print("ANSYS Fluent Contour Post-Processing Journal Exporter")
    print("=" * 70)

    # Generate journal content
    journal_content, num_cases = generate_journal_content()

    print(f"  Config:     {CONFIG_NAME}")
    print(f"  AoA Steps:  {num_cases}")
    print(f"  Variables:  {', '.join(CONTOUR_VARIABLES.values())}")

    if IMAGE_OUTPUT_DIR:
        print(f"  Output Dir: {IMAGE_OUTPUT_DIR}")
    else:
        print(f"  Output Dir: Saved alongside each case file")

    # Export the journal
    print("\nExporting contour journal file...")
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
