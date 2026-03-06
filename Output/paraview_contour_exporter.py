r"""
Automated ParaView Contour Exporter (pvpython)
==============================================
This script automatically crawled Fluent AoA directories, loads 
.cas.h5 and .dat.h5 files into ParaView, applies colormaps, 
and exports high-resolution contour plots without Fluent's TUI.

Usage:
    Run this script using ParaView's python engine (pvpython), NOT standard python.
    "C:\Program Files\ParaView 6.1.0\bin\pvpython.exe" paraview_contour_exporter.py
    & "C:\Program Files\ParaView 6.1.0\bin\pvpython.exe" "c:\Users\lukek\OneDrive - Liberty University\Group-F.L.U.I.D. Research - GRID-FINS - GRID-FINS\Python\Output\paraview_contour_exporter.py"
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
# List of parent directories containing the AoA_* folders.
# Each entry is processed in order with its matching CONFIG_NAME and IMAGE_OUTPUT_DIR. Singular, should not be taking multipile families
BASE_CASE_DIRS = [
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414.6.5.6\5.6.1.1.G",
]

# Configuration names (must match the order/length of BASE_CASE_DIRS)
CONFIG_NAMES = [
    "5.6.1.1.G",
]

# Where to save the high-res PNG contour images (must match the order/length of BASE_CASE_DIRS)
IMAGE_OUTPUT_DIRS = [   
    r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.5\5.6.1.1.G\Countour_Plots\ParaView\Streamlines",
]

# List of AoA values to process. Leave empty [] to auto-discover all AoA_* folders
AOA_LIST = [16]

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
    #"Velocity_Magnitude": "Velocity_Magnitude"
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
# REFERENCE_AOA: The AoA (degrees) at which you calibrated these camera views.
# The camera will automatically track the airfoil as it rotates to other AoAs.
# Set to 0 if you set up the views with the airfoil at 0 degrees.
REFERENCE_AOA = 5
CUSTOM_VIEWS = {
    "airfoil_center": {
        "Position": [0.27645901732693606, 0.008305101050527012, 5.945396079401388],
        "FocalPoint": [0.27645901732693606, 0.008305101050527012, 0.42671999335289],
        "ParallelScale": 0.2568992296621107  # Adjust this to control how "zoomed in" the parallel view is
    },
    "leading_edge_zoom": {
        "Position": [-0.0005004547891817193, 0.003047385406824787, 5.945396079401388],  # Example: Moved left towards the leading edge
        "FocalPoint": [-0.0005004547891817193, 0.003047385406824787, 0.42671999335289],
        "ParallelScale":0.06764959637718926  # Very zoomed in
    },
    "trailing_edge_zoom": {
        "Position": [0.3359936486721706, 0.003799047588793557, 5.945396079401388],  # Example: Moved left towards the leading edge
        "FocalPoint": [0.3359936486721706, 0.003799047588793557, 0.42671999335289],
        "ParallelScale": 0.12  # Very zoomed in
    }
}

# Which views to apply to which variable (can be one or multiple in a list!):
VARIABLE_VIEWS = {
    #"SV_P": ["airfoil_center", "leading_edge_zoom"],
    #"Velocity_Magnitude": ["trailing_edge_zoom", "airfoil_center"]
}

# Which views should shift vertically to track the airfoil across AoAs.
# Views NOT listed here will use their exact fixed camera positions.
AOA_TRACKING_VIEWS = ["trailing_edge_zoom"]

# --- 4. Color Re-Scaling (For GIF Stability) ---
# By default, ParaView recalculates the Min/Max color limits for EVERY Angle of Attack.
# This causes the global fluid color (like blue pressure) to "flash" drastically in GIFs.
# To lock the colors consistently across all AoAs, define your absolute Min/Max values here!
# Leave a variable OUT of this dictionary to let it auto-scale instead.
VARIABLE_RANGES = {
    "SV_P": [-370,140], # -370 and 140 for Velocity 14.3773,-1300 and 400 for 24.38
    "Velocity_Magnitude": [-1.5, 22] # -1.5 and 22 for 14.3773, -14 and 38 for 24.38
}

# --- 5. Image Output Settings ---
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
BACKGROUND_COLOR = [1.0, 1.0, 1.0]  # White

# --- 6. Streamline Settings ---
# Set to True to also render streamline plots for each AoA
ENABLE_STREAMLINES = True

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
STREAMLINE_SHOW_SURFACE = True
STREAMLINE_SURFACE_OPACITY = 0.3  # 0.0 = invisible, 1.0 = fully opaque
STREAMLINE_SURFACE_COLOR = [0.8, 0.8, 0.8]  # Light gray


# ============================================================
# SCRIPT LOGIC
# ============================================================

def adjust_camera_for_aoa(view_settings, current_aoa, reference_aoa):
    """
    Shift camera Position and FocalPoint vertically to follow the airfoil.
    
    As the airfoil is counter-rotated by -AoA, its center drops in Y.
    This computes the Y offset from the reference AoA and shifts the camera
    down (or up) to keep the airfoil centered. No camera rotation — just a
    pure vertical translation.
    
    Returns new (Position, FocalPoint) lists. Z and ParallelScale stay the same.
    """
    # How much the focal point's X position drops in Y due to rotation
    # Point (x, y) rotated by θ: new_y = x*sin(θ) + y*cos(θ)
    # Delta from reference: we compute the Y shift at both AoAs and take the difference
    ref_rad = math.radians(-reference_aoa)
    cur_rad = math.radians(-current_aoa)
    
    pos = list(view_settings["Position"])
    foc = list(view_settings["FocalPoint"])
    
    # Use the focal point X as the tracking coordinate (where the airfoil feature is)
    track_x = foc[0]
    track_y = foc[1]
    
    # Y position of the tracked point at reference vs. current AoA
    ref_y = track_x * math.sin(ref_rad) + track_y * math.cos(ref_rad)
    cur_y = track_x * math.sin(cur_rad) + track_y * math.cos(cur_rad)
    
    dy = cur_y - ref_y  # Negative means the airfoil dropped
    
    # Shift both position and focal point by the same Y offset
    pos[1] += dy
    foc[1] += dy
    
    return pos, foc

def discover_aoa_folders(base_dir):
    """Auto-discover AoA values from AoA_* folders in base_dir."""
    aoa_values = []
    aoa_pattern = re.compile(r'^AoA_(-?\d+\.?\d*)$')
    
    if not os.path.exists(base_dir):
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
        # Otherwise, dynamically auto-scale to just this specific AoA's data
        colorMap.RescaleTransferFunctionToDataRange(True)
    
    return renderView


def render_streamlines(smoother, aoa, aoa_str, config_name, image_output_dir):
    """
    Renders streamline visualizations for the current AoA case.
    
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
            
            if view_name in AOA_TRACKING_VIEWS:
                adj_pos, adj_foc = adjust_camera_for_aoa(
                    view_settings, float(aoa), REFERENCE_AOA
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
        
        aoa_output_dir = os.path.join(image_output_dir, f"AoA_{aoa_str}")
        os.makedirs(aoa_output_dir, exist_ok=True)
        
        output_file = os.path.join(aoa_output_dir, f"{config_name}_AoA_{aoa_str}_Streamlines_{view_name}.png")
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

        # 1. Determine AoA List
        aoa_list = AOA_LIST
        if not aoa_list:
            print("AOA_LIST is empty — auto-discovering AoA folders...")
            aoa_list = discover_aoa_folders(base_case_dir)
            if not aoa_list:
                print(f"[WARNING] No AoA_* folders found in {base_case_dir}. Skipping this directory.")
                continue
        print(f"Found {len(aoa_list)} AoA cases to process: {aoa_list}")

        # 2. Make Output Directory
        os.makedirs(image_output_dir, exist_ok=True)

        # 3. Process Each AoA Case
        for aoa in aoa_list:
            aoa_str = str(aoa) if isinstance(aoa, int) else f"{aoa}"
            print(f"\n--- Loading AoA: {aoa_str} ---")
            
            case_dir = os.path.join(base_case_dir, f"AoA_{aoa_str}")
            case_file = os.path.join(case_dir, f"{config_name}.{aoa_str}.cas.h5")
            
            if not os.path.exists(case_file):
                print(f"  [WARNING] Case file not found: {case_file}. Skipping.")
                continue

            fluentCase = FluentCFFCaseReader(registrationName=f"AoA_{aoa_str}_Data", FileName=case_file)
            
            # ACTUALLY parse the file data from the hard drive
            fluentCase.UpdatePipeline()
            
            # Rotate the geometry so the airfoil is flat
            transform = Transform(registrationName="Rotated_Airfoil", Input=fluentCase)
            # Fluent AOA is usually a rotation of the incoming flow, meaning the airfoil is technically flat,
            # but if the airfoil itself was rotated, we counter-rotate it here around the Z axis:
            transform.Transform.Rotate = [0.0, 0.0, -float(aoa)]
            transform.UpdatePipeline()

            # SMOOTHING STEP: Fluent data is usually "Cell Data" (blocky).
            # We must interpolate it to "Point Data" (vertices) so ParaView can draw smooth gradients
            # instead of seeing the borders of the mesh cells!
            smoother = CellDatatoPointData(registrationName="Smoothed_Data", Input=transform)
            smoother.ProcessAllArrays = 1
            smoother.UpdatePipeline()

            # Calculate Velocity Magnitude from U, V, W components (now using interpolated Point Data)
            calculator = Calculator(registrationName="Velocity_Calculator", Input=smoother)
            calculator.AttributeType = 'Point Data'
            calculator.ResultArrayName = 'Velocity_Magnitude'
            calculator.Function = 'sqrt(SV_U^2 + SV_V^2 + (SV_W^2))'
            calculator.UpdatePipeline()
            
            # Render each requested variable
            for var_fluent, var_label in VARIABLES_TO_PLOT.items():
                print(f"  -> Rendering {var_label}...")
                
                # Setup colors and display using the calculated data
                renderView = setup_paraview_scene(calculator, var_fluent)
                
                # Convert to list if user accidentally just put a single string
                views_to_render = VARIABLE_VIEWS.get(var_fluent, ["airfoil_center"])
                if isinstance(views_to_render, str):
                    views_to_render = [views_to_render]
                
                # --- CAMERA ANGLE SECTION ---
                for view_name in views_to_render:
                    # Set parallel projection for true 2D looking plots (no perspective distortion)
                    renderView.CameraParallelProjection = 1
                    
                    # Check if this view exists in CUSTOM_VIEWS
                    if view_name in CUSTOM_VIEWS:
                        # Force a render first so ParaView initializes the view bounds
                        Render(renderView)
                        
                        view_settings = CUSTOM_VIEWS[view_name]
                        
                        # Only shift camera for views listed in AOA_TRACKING_VIEWS
                        if view_name in AOA_TRACKING_VIEWS:
                            adj_pos, adj_foc = adjust_camera_for_aoa(
                                view_settings, float(aoa), REFERENCE_AOA
                            )
                            renderView.CameraPosition = adj_pos
                            renderView.CameraFocalPoint = adj_foc
                        else:
                            renderView.CameraPosition = view_settings["Position"]
                            renderView.CameraFocalPoint = view_settings["FocalPoint"]
                        
                        renderView.CameraParallelScale = view_settings["ParallelScale"]
                        
                        # Update the camera explicitly
                        renderView.Update()
                        
                        print(f"    (Applied custom view: {view_name})")
                    else:
                        # Fallback: Just fit the whole domain to the screen
                        renderView.ResetCamera() 
                    
                    # Render and Save Picture
                    RenderAllViews()
                    
                    # Save into individual AoA folders
                    aoa_output_dir = os.path.join(image_output_dir, f"AoA_{aoa_str}")
                    os.makedirs(aoa_output_dir, exist_ok=True)
                    
                    # Output filename now includes the view name so they don't overwrite each other!
                    output_file = os.path.join(aoa_output_dir, f"{config_name}_AoA_{aoa_str}_{var_label}_{view_name}.png")
                    SaveScreenshot(output_file, renderView, ImageResolution=[RESOLUTION_X, RESOLUTION_Y])
                
                # Clean up the view so variables don't overlap on the next loop iteration
                Hide(calculator, renderView)

            # --- STREAMLINE RENDERING ---
            if ENABLE_STREAMLINES:
                render_streamlines(smoother, aoa, aoa_str, config_name, image_output_dir)

            # Destroy the loaded data objects to free up RAM before the next AoA
            Delete(calculator)
            Delete(smoother)
            Delete(transform)
            Delete(fluentCase)
            del calculator, smoother, transform, fluentCase

    print("\n[OK] ParaView processing completed successfully!")
    print(f"Images saved to directories: {IMAGE_OUTPUT_DIRS}")


if __name__ == "__main__":
    main()
