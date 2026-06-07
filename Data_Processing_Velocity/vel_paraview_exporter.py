r"""
Automated ParaView Contour Exporter (pvpython)
==============================================
This script automatically crawled Fluent Mach directories, loads 
.cas.h5 and .dat.h5 files into ParaView, applies colormaps, 
and exports high-resolution contour plots without Fluent's TUI.

Usage:
    Run this script using ParaView's python engine (pvpython), NOT standard python.
    "C:\\Program Files\\ParaView 6.1.0\\bin\\pvpython.exe" vel_paraview_exporter.py
    & "C:\\Program Files\\ParaView 6.1.0\\bin\\pvpython.exe" "vel_paraview_exporter.py"
    
    This is to be run after post prcoessing is done, take the individuall families and run them
"""

import os
import re
import math

try:
    from paraview.simple import *
except ImportError:
    print("[ERROR] You must run this script using ParaView's 'pvpython.exe', not standard Python!")
    import sys
    sys.exit(1)

# ============================================================
# CONFIGURATION - MODIFY THIS SECTION
# ============================================================

# --- 1. Base Locations & Naming ---
# List of parent directories containing the Mach_* folders.
# Each entry is processed in order with its matching CONFIG_NAME and IMAGE_OUTPUT_DIR. Singular, should not be taking multipile families
BASE_CASE_DIRS = [
    # r"C:\path\to\your\data\1.2.1.2.NG",
]

# Configuration names (must match the order/length of BASE_CASE_DIRS)
CONFIG_NAMES = [
    "1.2.1.2.NG",
]

# Where to save the high-res PNG contour images (must match the order/length of BASE_CASE_DIRS)
IMAGE_OUTPUT_DIRS = [   
    # r"C:\path\to\your\output\1.2.1.2.NG\Countour_Plots\ParaView",
]

# List of Mach values to process. Leave empty [] to auto-discover all Mach folders
MACH_LIST = []

# --- 2. Variables and Colors ---
# Which variables to plot. Note: ParaView might capitalize Fluent variables
# Check inside ParaView GUI for exact names if these fail.
# The second value is what the graphs will be labeled as.
# "SV_P": "Pressure_Static"
# "Velocity_Magnitude": "Velocity_Magnitude"
# "SV_T": "Temperature"
# "SV_Y_PLUS": "Y_Plus"
# "SV_Skin_Friction_Coefficient": "Skin_Friction_Coefficient"
# Example: "Pressure", "Velocity Magnitude", "Skin Friction Coefficient"
VARIABLES_TO_PLOT = {
    #"SV_P": "Pressure_Static",
    "Velocity_Magnitude": "Velocity_Magnitude",
    "Mach_Number": "Mach_Number"
}

# The Colormap preset to use. "Viridis (matplotlib)" is standard. 
# "Cool to Warm" is another great option for Pressure.
COLORMAP_NAME = "Cool to Warm"

# --- 3. Camera Views ---
# Define specific zoom angles and locations based on your airfoil and mesh.
# Format: "ViewName": {"Position": [x,y,z], "FocalPoint": [x,y,z], "ParallelScale": float}
# 
# How to get these numbers:
# 1. Open ParaView manually and load one of your cases.
# 2. Adjust your camera to exactly where you want it.
# 3. In the toolbar, click "Adjust Camera" (the camera icon with a little gear).
# 4. Copy the "Camera Position" and "Focal Point" numbers into the dictionary below.
# 5. If using 2D Parallel Projection, copy the "Parallel Scale" value.
# Use tools start trace to get the camera position and focal point
#
# REFERENCE_MACH: The Mach number at which you calibrated these camera views.
# The camera will automatically track the airfoil as it rotates to other Mach numbers.
# Set to 0 if you set up the views with the airfoil at 0 degrees.
#REFERENCE_MACH = 0.0
CUSTOM_VIEWS = {
    "rocket_center": {
        "Position": [0.7424588203430176, -1.2962841987609837, -28.317022313687893],
        "FocalPoint": [0.9309403578196692, 1.6695282291804414, -0.9662936305007656],
        "ParallelScale": 2  # Adjust this to control how "zoomed in" the parallel view is
    },
    "nose_cone_zoom": {
        "Position": [0.7424588203430176, -1.2962841987609837, -28.317022313687893],  # Example: Moved left towards the leading edge
        "FocalPoint": [0.6997880334720208, 3.0038919986204538, -2.962237672544282],
        "ParallelScale":1  # Very zoomed in
    },
    "fins_zoom": {
        "Position": [0.8337072418449709, -10.491903004141665, -82.53641327595919],  # Example: Moved left towards the leading edge
        "FocalPoint": [0.7407496759448634, 0.08788099655558666, -4.078036480277453],
        "ParallelScale": 1  # Very zoomed in
    }
    
}

# Which views to apply to which variable (can be one or multiple in a list!):
VARIABLE_VIEWS = {
    #"SV_P": ["rocket_center", "nose_cone_zoom"],
    "Velocity_Magnitude": ["rocket_center", "nose_cone_zoom", "fins_zoom"],
    "Mach_Number": ["rocket_center", "nose_cone_zoom", "fins_zoom"]
}

# Which views should shift vertically to track the airfoil across Mach numbers.
# Views NOT listed here will use their exact fixed camera positions.
MACH_TRACKING_VIEWS = []

# --- 4. Color Re-Scaling (For GIF Stability) ---
# By default, ParaView recalculates the Min/Max color limits for EVERY Angle of Attack.
# This causes the global fluid color (like blue pressure) to "flash" drastically in GIFs.
# To lock the colors consistently across all Mach numbers, define your absolute Min/Max values here!
# Leave a variable OUT of this dictionary to let it auto-scale instead.
VARIABLE_RANGES = {
    "SV_P": [-370,140], # -370 and 140 for Mach 14.3773,-1300 and 400 for 24.38
    "Velocity_Magnitude": [-180,400], # -1.5 and 22 for Mach 14.3773, -14 and 38 for 24.38
    "Mach_Number": [0.0, 1.5]
}

# --- 5. Image Output Settings ---
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
BACKGROUND_COLOR = [1.0, 1.0, 1.0]  # White

# --- 6. Streamline Settings ---
# Set to True to also render streamline plots for each Mach number
ENABLE_STREAMLINES = False  

# Seed line: streamlines will be seeded along this line segment.
# Format: [x, y, z] for each endpoint.
# A vertical line upstream of the airfoil is a good default.
STREAMLINE_SEED_POINT1 = [-0.05, -0.50, 0.0]  # Bottom of seed line
STREAMLINE_SEED_POINT2 = [0.05,  0.50, 0.0]  # Top of seed line
STREAMLINE_SEED_RESOLUTION = 100  # Number of seed points along the line

# Integration settings
STREAMLINE_MAX_LENGTH = 50.0  # Maximum streamline propagation length
STREAMLINE_DIRECTION = "FORWARD"  # "FORWARD", "BACKWARD", or "BOTH"
# Visual styling
STREAMLINE_USE_TUBES = True      # True = render as 3D tubes, False = thin lines
STREAMLINE_TUBE_RADIUS = 0.001   # Tube thickness (only if USE_TUBES is True)
STREAMLINE_COLOR_BY_SPEED = True  # True = color by velocity magnitude, False = solid color
STREAMLINE_SOLID_COLOR = [0.0, 0.0, 0.0]  # RGB solid color if not coloring by speed

# Which camera views to use for streamline screenshots.
# Uses the same CUSTOM_VIEWS definitions from Section 3.
STREAMLINE_VIEWS = ["airfoil_center"]

# Whether to show the surface geometry underneath the streamlines
STREAMLINE_SHOW_SURFACE = False
STREAMLINE_SURFACE_OPACITY = 0.3  # 0.0 = invisible, 1.0 = fully opaque
STREAMLINE_SURFACE_COLOR = [0.8, 0.8, 0.8]  # Light gray


# ============================================================
# SCRIPT LOGIC
# ============================================================

def adjust_camera_for_mach(view_settings, current_mach, reference_mach):
    """
    Shift camera Position and FocalPoint vertically to follow the airfoil.
    
    As the airfoil is counter-rotated by -Mach, its center drops in Y.
    This computes the Y offset from the reference Mach and shifts the camera
    down (or up) to keep the airfoil centered. No camera rotation — just a
    pure vertical translation.
    
    Returns new (Position, FocalPoint) lists. Z and ParallelScale stay the same.
    """
    # How much the focal point's X position drops in Y due to rotation
    # Point (x, y) rotated by θ: new_y = x*sin(θ) + y*cos(θ)
    # Delta from reference: we compute the Y shift at both Mach numbers and take the difference
    ref_rad = math.radians(-reference_mach)
    cur_rad = math.radians(-current_mach)
    
    pos = list(view_settings["Position"])
    foc = list(view_settings["FocalPoint"])
    
    # Use the focal point X as the tracking coordinate (where the airfoil feature is)
    track_x = foc[0]
    track_y = foc[1]
    
    # Y position of the tracked point at reference vs. current Mach
    ref_y = track_x * math.sin(ref_rad) + track_y * math.cos(ref_rad)
    cur_y = track_x * math.sin(cur_rad) + track_y * math.cos(cur_rad)
    
    dy = cur_y - ref_y  # Negative means the airfoil dropped
    
    # Shift both position and focal point by the same Y offset
    pos[1] += dy
    foc[1] += dy
    
    return pos, foc

def discover_mach_folders(base_dir):
    """Auto-discover Mach values from Mach_* folders in base_dir."""
    mach_values = []
    mach_pattern = re.compile(r'^Mach_(-?\d+\.?\d*)$')
    
    if not os.path.exists(base_dir):
        print(f"  [WARNING] Base directory not found: {base_dir}")
        return mach_values
    
    for entry in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, entry)):
            match = mach_pattern.match(entry)
            if match:
                val = float(match.group(1))
                if val == int(val):
                    val = int(val)
                mach_values.append(val)
    
    mach_values.sort(key=lambda x: float(x))
    return mach_values


def setup_paraview_scene(data_source, var_fluent_name):
    """Sets up the ParaView display representation for a specific variable."""
    # Get active view
    renderView = GetActiveViewOrCreate('RenderView')
    renderView.ViewSize = [RESOLUTION_X, RESOLUTION_Y]
    renderView.Background = BACKGROUND_COLOR
    
    # Hide the XYZ orientation axes triad in the bottom left corner
    renderView.OrientationAxesVisibility = 0
    
    # Create a display representation of the Fluent data
    display = Show(data_source, renderView, 'UnstructuredGridRepresentation')
    
    # Set the mathematical model to look nice (hide mesh lines)
    display.Representation = 'Surface'
    
    # Tell ParaView to color the surface by the specified variable
    # We use POINTS instead of CELLS now because we smoothed the data!
    ColorBy(display, ('POINTS', var_fluent_name))
    
    # Show the color legend (scalar bar)
    display.SetScalarBarVisibility(renderView, True)
    
    # Fetch the color transfer function and apply our beautiful preset
    colorMap = GetColorTransferFunction(var_fluent_name)
    colorMap.ApplyPreset(COLORMAP_NAME, True)
    
    # Rescale color map to the data range natively
    # If the user specified a custom hard-locked range, use it!
    if var_fluent_name in VARIABLE_RANGES:
        min_val, max_val = VARIABLE_RANGES[var_fluent_name]
        colorMap.RescaleTransferFunction(min_val, max_val)
        
        # Also rescale the opacity map (if it's being used) to match
        opacityMap = GetOpacityTransferFunction(var_fluent_name)
        opacityMap.RescaleTransferFunction(min_val, max_val)
    else:
        # Otherwise, dynamically auto-scale to just this specific Mach's data
        colorMap.RescaleTransferFunctionToDataRange(True)
    
    return renderView


def render_streamlines(smoother, mach, mach_str, config_name, image_output_dir):
    """
    Renders streamline visualizations for the current Mach case.
    
    Uses the smoothed data (Point Data) to build a velocity vector,
    then traces streamlines from a configurable seed line.
    """
    print(f"  -> Rendering Streamlines...")
    
    renderView = GetActiveViewOrCreate('RenderView')
    renderView.ViewSize = [RESOLUTION_X, RESOLUTION_Y]
    renderView.Background = BACKGROUND_COLOR
    renderView.OrientationAxesVisibility = 0
    
    # --- Build a velocity vector from Fluent's separate U, V, W components ---
    vecCalc = Calculator(registrationName="Velocity_Vector", Input=smoother)
    vecCalc.AttributeType = 'Point Data'
    vecCalc.ResultArrayName = 'VelocityVec'
    vecCalc.Function = 'SV_U*iHat + SV_V*jHat + SV_W*kHat'
    vecCalc.UpdatePipeline()
    
    # --- Create streamlines using StreamTracer ---
    streamTracer = StreamTracer(registrationName="Streamlines", Input=vecCalc,
                                SeedType='Line')
    
    # Configure the seed line
    streamTracer.SeedType.Point1 = STREAMLINE_SEED_POINT1
    streamTracer.SeedType.Point2 = STREAMLINE_SEED_POINT2
    streamTracer.SeedType.Resolution = STREAMLINE_SEED_RESOLUTION
    
    # Configure integration
    streamTracer.MaximumStreamlineLength = STREAMLINE_MAX_LENGTH
    streamTracer.IntegrationDirection = {"FORWARD": 0, "BACKWARD": 1, "BOTH": 2}.get(STREAMLINE_DIRECTION.upper(), 2)
    
    streamTracer.UpdatePipeline()
    
    # --- Optionally apply Tube filter for better visibility ---
    if STREAMLINE_USE_TUBES:
        tubeFilter = Tube(registrationName="StreamlineTubes", Input=streamTracer)
        tubeFilter.Radius = STREAMLINE_TUBE_RADIUS
        tubeFilter.NumberofSides = 12
        tubeFilter.UpdatePipeline()
        displaySource = tubeFilter
    else:
        tubeFilter = None
        displaySource = streamTracer
    
    # --- Show the surface geometry underneath (optional) ---
    surfaceDisplay = None
    if STREAMLINE_SHOW_SURFACE:
        surfaceDisplay = Show(smoother, renderView, 'UnstructuredGridRepresentation')
        surfaceDisplay.Representation = 'Surface'
        surfaceDisplay.Opacity = STREAMLINE_SURFACE_OPACITY
        surfaceDisplay.DiffuseColor = STREAMLINE_SURFACE_COLOR
        surfaceDisplay.MapScalars = 0  # Disable scalar coloring entirely
        surfaceDisplay.AmbientColor = STREAMLINE_SURFACE_COLOR
        surfaceDisplay.DiffuseColor = STREAMLINE_SURFACE_COLOR
    
    # --- Display the streamlines ---
    streamDisplay = Show(displaySource, renderView)
    streamDisplay.Representation = 'Surface'
    
    if STREAMLINE_COLOR_BY_SPEED:
        # Color streamlines by velocity magnitude
        ColorBy(streamDisplay, ('POINTS', 'VelocityVec', 'Magnitude'))
        streamDisplay.SetScalarBarVisibility(renderView, True)
        colorMap = GetColorTransferFunction('VelocityVec')
        colorMap.ApplyPreset(COLORMAP_NAME, True)
        if 'Velocity_Magnitude' in VARIABLE_RANGES:
            min_val, max_val = VARIABLE_RANGES['Velocity_Magnitude']
            colorMap.RescaleTransferFunction(min_val, max_val)
        else:
            colorMap.RescaleTransferFunctionToDataRange(True)
    else:
        # Solid color
        ColorBy(streamDisplay, None)
        streamDisplay.DiffuseColor = STREAMLINE_SOLID_COLOR
    
    # --- Render each camera view ---
    for view_name in STREAMLINE_VIEWS:
        renderView.CameraParallelProjection = 1
        
        if view_name in CUSTOM_VIEWS:
            Render(renderView)
            view_settings = CUSTOM_VIEWS[view_name]
            
            if view_name in MACH_TRACKING_VIEWS:
                adj_pos, adj_foc = adjust_camera_for_mach(
                    view_settings, float(mach), REFERENCE_MACH
                )
                renderView.CameraPosition = adj_pos
                renderView.CameraFocalPoint = adj_foc
            else:
                renderView.CameraPosition = view_settings["Position"]
                renderView.CameraFocalPoint = view_settings["FocalPoint"]
            
            renderView.CameraParallelScale = view_settings["ParallelScale"]
            renderView.Update()
            print(f"    (Applied custom view: {view_name})")
        else:
            renderView.ResetCamera()
        
        RenderAllViews()
        
        mach_output_dir = os.path.join(image_output_dir, f"mach_{mach_str}")
        os.makedirs(mach_output_dir, exist_ok=True)
        
        output_file = os.path.join(mach_output_dir, f"{config_name}_mach_{mach_str}_Streamlines_{view_name}.png")
        SaveScreenshot(output_file, renderView, ImageResolution=[RESOLUTION_X, RESOLUTION_Y])
        print(f"    Saved: {output_file}")
    
    # --- Cleanup ---
    Hide(displaySource, renderView)
    if surfaceDisplay:
        Hide(smoother, renderView)
    if tubeFilter:
        Delete(tubeFilter)
    Delete(streamTracer)
    Delete(vecCalc)
    del tubeFilter, streamTracer, vecCalc


def main():
    print("=" * 70)
    print("ParaView (pvpython) Contour Exporter")
    print("=" * 70)

    # Validate that all config lists are the same length
    if not (len(BASE_CASE_DIRS) == len(CONFIG_NAMES) == len(IMAGE_OUTPUT_DIRS)):
        print("[ERROR] BASE_CASE_DIRS, CONFIG_NAMES, and IMAGE_OUTPUT_DIRS must all have the same number of entries!")
        return

    # Disable automatic camera resets to keep our angles steady between loops
    paraview.simple._DisableFirstRenderCameraReset()

    # Process each directory entry
    for dir_idx, (base_case_dir, config_name, image_output_dir) in enumerate(
        zip(BASE_CASE_DIRS, CONFIG_NAMES, IMAGE_OUTPUT_DIRS)
    ):
        print(f"\n{'=' * 70}")
        print(f"Processing directory {dir_idx + 1}/{len(BASE_CASE_DIRS)}: {config_name}")
        print(f"  Source : {base_case_dir}")
        print(f"  Output : {image_output_dir}")
        print(f"{'=' * 70}")

        # 1. Determine Mach List
        mach_list = MACH_LIST
        if not mach_list:
            print("MACH_LIST is empty — auto-discovering Mach folders...")
            mach_list = discover_mach_folders(base_case_dir)
            if not mach_list:
                print(f"[WARNING] No Mach_* folders found in {base_case_dir}. Skipping this directory.")
                continue
        print(f"Found {len(mach_list)} Mach cases to process: {mach_list}")

        # 2. Make Output Directory
        os.makedirs(image_output_dir, exist_ok=True)

        # 3. Process Each Mach Case
        for mach in mach_list:
            mach_str = str(mach) if isinstance(mach, int) else f"{mach}"
            print(f"\n--- Loading Mach: {mach_str} ---")
            
            case_dir = os.path.join(base_case_dir, f"Mach_{mach_str}")
            case_file = os.path.join(case_dir, f"{config_name}.{mach_str}.cas.h5")
            
            if not os.path.exists(case_file):
                print(f"  [WARNING] Case file not found: {case_file}. Skipping.")
                continue

            fluentCase = FluentCFFCaseReader(registrationName=f"mach_{mach_str}_Data", FileName=case_file)
            
            # ACTUALLY parse the file data from the hard drive
            fluentCase.UpdatePipeline()
            
            # Rotate the geometry so the airfoil is flat (DISABLED for Mach plots)
            # transform = Transform(registrationName="Rotated_Airfoil", Input=fluentCase)
            # transform.Transform.Rotate = [0.0, 0.0, -float(mach)]
            # transform.UpdatePipeline()

            # SMOOTHING STEP: Fluent data is usually "Cell Data" (blocky).
            # We must interpolate it to "Point Data" (vertices) so ParaView can draw smooth gradients
            # instead of seeing the borders of the mesh cells!
            smoother = CellDatatoPointData(registrationName="Smoothed_Data", Input=fluentCase)
            smoother.ProcessAllArrays = 1
            smoother.UpdatePipeline()

            # Calculate Velocity Magnitude from U, V, W components (now using interpolated Point Data)
            calculator = Calculator(registrationName="Velocity_Calculator", Input=smoother)
            calculator.AttributeType = 'Point Data'
            calculator.ResultArrayName = 'Velocity_Magnitude'
            calculator.Function = 'sqrt(SV_U^2 + SV_V^2 + (SV_W^2))'
            calculator.UpdatePipeline()
            
            # Calculate Mach Number dynamically (speed of sound a = sqrt(gamma * R * T))
            mach_calculator = Calculator(registrationName="Mach_Calculator", Input=calculator)
            mach_calculator.AttributeType = 'Point Data'
            mach_calculator.ResultArrayName = 'Mach_Number'
            mach_calculator.Function = 'Velocity_Magnitude / sqrt(1.4 * 287.05 * SV_T)'
            mach_calculator.UpdatePipeline()
            
            # Render each requested variable
            for var_fluent, var_label in VARIABLES_TO_PLOT.items():
                print(f"  -> Rendering {var_label}...")
                
                # Setup colors and display using the calculated data
                renderView = setup_paraview_scene(mach_calculator, var_fluent)
                
                # Convert to list if user accidentally just put a single string
                views_to_render = VARIABLE_VIEWS.get(var_fluent, ["airfoil_center"])
                if isinstance(views_to_render, str):
                    views_to_render = [views_to_render]
                
                # --- CAMERA ANGLE SECTION ---
                for view_name in views_to_render:
                    # Check if this view exists in CUSTOM_VIEWS
                    if view_name in CUSTOM_VIEWS:
                        view_settings = CUSTOM_VIEWS[view_name]
                        
                        # Setup Parallel Projection
                        renderView.CameraParallelProjection = 1
                        
                        # Apply initial camera settings
                        renderView.CameraPosition = view_settings["Position"]
                        renderView.CameraFocalPoint = view_settings["FocalPoint"]
                        renderView.CameraParallelScale = view_settings["ParallelScale"]
                        # Default to User-Specified Orientation if not in dictionary
                        renderView.CameraViewUp = view_settings.get("ViewUp", [-1.0, 0.0, 0.0])
                        
                        # Force a render to initialize the scene, then RE-APPLY settings
                        # to ensure ParaView's automatic reset doesn't overwrite our custom view.
                        Render(renderView)
                        
                        renderView.CameraPosition = view_settings["Position"]
                        renderView.CameraFocalPoint = view_settings["FocalPoint"]
                        renderView.CameraParallelScale = view_settings["ParallelScale"]
                        renderView.CameraViewUp = view_settings.get("ViewUp", [-1.0, 0.0, 0.0])
                        
                        # Update the view explicitly
                        renderView.Update()
                        print(f"    (Applied custom view: {view_name})")
                    else:
                        # Fallback: Just fit the whole domain to the screen
                        print(f"    (View '{view_name}' not found in CUSTOM_VIEWS, resetting camera...)")
                        renderView.ResetCamera()
                        renderView.Update()                    
                    # Render and Save Picture
                    RenderAllViews()
                    
                    # Save into individual Mach folders
                    mach_output_dir = os.path.join(image_output_dir, f"mach_{mach_str}")
                    os.makedirs(mach_output_dir, exist_ok=True)
                    
                    # Output filename now includes the view name so they don't overwrite each other!
                    output_file = os.path.join(mach_output_dir, f"{config_name}_mach_{mach_str}_{var_label}_{view_name}.png")
                    SaveScreenshot(output_file, renderView, ImageResolution=[RESOLUTION_X, RESOLUTION_Y])
                
                # Clean up the view so variables don't overlap on the next loop iteration
                Hide(calculator, renderView)

            # --- STREAMLINE RENDERING ---
            if ENABLE_STREAMLINES:
                render_streamlines(smoother, mach, mach_str, config_name, image_output_dir)

            # Destroy the loaded data objects to free up RAM before the next Mach
            Delete(mach_calculator)
            Delete(calculator)
            Delete(smoother)
            # Delete(transform)
            Delete(fluentCase)
            del mach_calculator, calculator, smoother, fluentCase

    print("\n[OK] ParaView processing completed successfully!")
    print(f"Images saved to directories: {IMAGE_OUTPUT_DIRS}")


if __name__ == "__main__":
    main()
