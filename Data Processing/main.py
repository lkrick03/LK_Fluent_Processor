"""
CFD Data Processing - Main Execution Script
Consolidates all 4 notebooks into a single executable workflow.

This script:
1. Loads and processes CFD simulation data
2. (Optional) Runs convergence analysis
3. Generates Excel summary files
4. Creates coefficient graphs

Author: Luke Krick
Date: February 2026
"""

from pathlib import Path
import numpy as np
import pandas as pd
from cfd_functions import (
    load_lift_drag_data, compute_statistics, extract_aoa_number,
    analyze_convergence, plot_convergence_analysis, plot_convergence_summary, create_data_summary_sheet, create_turbulence_comparison_sheet,
    create_version_comparison_sheet, create_coefficients_sheet, create_optimized_statistics_sheet, apply_excel_formatting,
    create_coefficient_graphs, create_expanded_graphs, apply_data_manipulations, get_simulation_family_name,
    read_fluent_xy, plot_xy_series
)
from config import POSITION_MAP, VALUE_MAPPINGS, COMPARISON_CONFIGS, DATA_MANIPULATIONS, NAMING_SCHEMAS, ACTIVE_SCHEMA


# ==================== USER CONFIGURATION ====================

# Input/Output Directories
# DATA_SOURCES acts as a priority list. If duplicates exist, the one with the higher Version number wins.
# If versions are identical, they are treated as duplicates (this script logic handles versioning, not path priority).
DATA_SOURCES = [
    Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.3.NG"),
    Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.4.NG"),
    Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.5.NG"),
    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.3.G"),
    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.4.G"),
    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.5.G"),
    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.6.G"),

    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.1.2"),
    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.2.1"),
    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.3.1"),

    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.2.1.G"),
    #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414_006_004.3\4.3.2.1.NG"),

    Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414.6.4.6\4.6.1.1.NG")

    #Path(r"C:\Path\To\Newer\Reruns"), 
]
OUTPUT_DIR = Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\Processed_Data\Comparisons\2414_006_004\Mesh_Comparison\4.6_vs_4.3")

# Configuration Extraction Method
CONFIG_EXTRACTION_METHOD = 'case_file'  # Options: 'case_file' or 'folder'

# Comparison Mode
# Options: 'default', 'turbulence', 'grid', 'mesh', 'version', 'expanded'
# - default: Standard behavior (highest version wins).
# - turbulence: Groups by Geometry.Mesh to compare turbulence models side-by-side.
# - grid: Groups by Geometry.Mesh.Turbulence to compare Grid vs No Grid side-by-side.
# - mesh: Groups by Geometry.Turbulence.Grid to compare mesh types (Medium, Adapted, Fine...) side-by-side.
# - version: Groups by Geometry.Mesh.Turbulence.Grid to compare versions (V1, V2...) side-by-side.
# - expanded: Groups by Geometry.Mesh to calculate and compare Grid Efficiency Ratios (L/D Improvement) across turbulence models.
COMPARISON_MODE = 'mesh'

# AoA Filter: Set to a list of angles (e.g., [0, 2, 4]) to only process those AoAs.
# Set to [] or None to process all.
AOA_FILTER = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]

# Path to folder containing .xy files (if not in source folders)
# Only runs when in default comparison mode
XY_DATA_SOURCE_DIR = Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fleunt\Directories\2414.6.4.6\4.6.1.1.NG\y_plus_pressure_data")

# Processing Parameters
NUM_ITERATIONS = 150  # Number of last iterations to use for statistics
RUN_CONVERGENCE_ANALYSIS = True  # Set to False to skip convergence analysis
CONVERGENCE_MAX_TRIM = 0.9  # Maximum fraction of data to trim (0.8 = 80%)
CONVERGENCE_NUM_TESTS = 25  # Number of trim amounts to test
GRAPH_MAX_COV = 50  # Data points with COV > 5% will be excluded from graphs

# Coefficient Calculation Parameters
SPAN = 0.85344 # [m] Test width is 2.8 feet
CHORD = 0.3048 # [m] Test chord is 1 foot
AIR_DENSITY = 1.225 # [kg/m^3] Standard sea level air density
VELOCITY = 24.384 # [m/s] Test velocity is 80 ft/s

REFERENCE_AREA = SPAN * CHORD
DYNAMIC_PRESSURE = 0.5 * AIR_DENSITY * VELOCITY**2
Q_TIMES_A = DYNAMIC_PRESSURE * REFERENCE_AREA

# Reynolds Number Calculation
VISCOSITY = 1.7894e-5  # [kg/(m·s)] Dynamic viscosity of air at sea level (15°C)
REYNOLDS_NUMBER = (AIR_DENSITY * VELOCITY * CHORD) / VISCOSITY
print(f"Reynolds Number: {REYNOLDS_NUMBER:,.0f}")

# ==================== MAIN WORKFLOW ====================

def export_force_data(filepath, data, metadata, force_type):
    """Helper to export force data to text file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Configuration: {metadata['config']} | AoA: {metadata['aoa']} | Turbulence: {metadata['turbulence_model']}\n")
        f.write(f"# Geometry: {metadata['geometry']} | Mesh: {metadata['mesh']} | Grid: {metadata['grid']}\n")
        f.write(f"# Total Points: {len(data)}\n#\n")
        np.savetxt(f, data, fmt='%.6f')

def main(config=None):
    """Main execution function.
    
    Args:
        config: Optional dict of settings (from GUI). When None, uses
                the module-level constants defined above, so running
                ``python main.py`` directly is unchanged.
    """
    # ── Config override: GUI passes a dict, CLI uses module-level globals ──
    if config:
        _DATA_SOURCES           = config["data_sources"]
        _OUTPUT_DIR             = config["output_dir"]
        _CONFIG_EXTRACTION_METHOD = config["config_extraction_method"]
        _COMPARISON_MODE        = config["comparison_mode"]
        _AOA_FILTER             = config.get("aoa_filter")
        _XY_DATA_SOURCE_DIR     = config.get("xy_data_source_dir", XY_DATA_SOURCE_DIR)
        _NUM_ITERATIONS         = config["num_iterations"]
        _RUN_CONVERGENCE        = config["run_convergence_analysis"]
        _CONVERGENCE_MAX_TRIM   = config["convergence_max_trim"]
        _CONVERGENCE_NUM_TESTS  = config["convergence_num_tests"]
        _GRAPH_MAX_COV          = config["graph_max_cov"]
        _Q_TIMES_A              = config["q_times_a"]
        _REYNOLDS_NUMBER        = config.get("reynolds_number", REYNOLDS_NUMBER)
        # config.py settings (may be overridden by schema choice)
        from config import NAMING_SCHEMAS as _ALL_SCHEMAS
        _schema = config.get("active_schema", ACTIVE_SCHEMA)
        _POSITION_MAP           = _ALL_SCHEMAS[_schema]
        _VALUE_MAPPINGS         = VALUE_MAPPINGS  # shared, not overridden
        _COMPARISON_CONFIGS     = COMPARISON_CONFIGS
        _DATA_MANIPULATIONS     = DATA_MANIPULATIONS
    else:
        _DATA_SOURCES           = DATA_SOURCES
        _OUTPUT_DIR             = OUTPUT_DIR
        _CONFIG_EXTRACTION_METHOD = CONFIG_EXTRACTION_METHOD
        _COMPARISON_MODE        = COMPARISON_MODE
        _AOA_FILTER             = AOA_FILTER
        _XY_DATA_SOURCE_DIR     = XY_DATA_SOURCE_DIR
        _NUM_ITERATIONS         = NUM_ITERATIONS
        _RUN_CONVERGENCE        = RUN_CONVERGENCE_ANALYSIS
        _CONVERGENCE_MAX_TRIM   = CONVERGENCE_MAX_TRIM
        _CONVERGENCE_NUM_TESTS  = CONVERGENCE_NUM_TESTS
        _GRAPH_MAX_COV          = GRAPH_MAX_COV
        _Q_TIMES_A              = Q_TIMES_A
        _REYNOLDS_NUMBER        = REYNOLDS_NUMBER
        _POSITION_MAP           = POSITION_MAP
        _VALUE_MAPPINGS         = VALUE_MAPPINGS
        _COMPARISON_CONFIGS     = COMPARISON_CONFIGS
        _DATA_MANIPULATIONS     = DATA_MANIPULATIONS
    
    print("=" * 100)
    print("CFD DATA PROCESSING - CONSOLIDATED WORKFLOW")
    print("=" * 100)
    
    # ==================== PART 1: LOAD AND PROCESS DATA ====================
    print("\n" + "=" * 100)
    print("PART 1: LOADING AND PROCESSING DATA")
    print("=" * 100)
    
    print(f"\nLoading data from {len(_DATA_SOURCES)} sources...")
    for src in _DATA_SOURCES:
        print(f"  - {src}")

    all_data, validation_report = load_lift_drag_data(_DATA_SOURCES, _CONFIG_EXTRACTION_METHOD, _POSITION_MAP, _VALUE_MAPPINGS, comparison_mode=_COMPARISON_MODE)
    
    # Apply Quick AoA Filter if set
    if _AOA_FILTER:
        print(f"\n⚡ Applying AoA Filter: {_AOA_FILTER}")
        initial_count = len(all_data)
        filtered_data = {}
        for key, value in all_data.items():
            # key is (config, aoa_str)
            # We need to extract number from aoa_str (e.g. "AoA_0" -> 0)
            if extract_aoa_number(key[1]) in _AOA_FILTER:
                 filtered_data[key] = value
        
        all_data = filtered_data
        print(f"   -> Filtered down to {len(all_data)} simulations (removed {initial_count - len(all_data)})")
    
    # Print validation report
    print("\n" + "-" * 100)
    print("DATA VALIDATION REPORT")
    print("-" * 100)
    print(f"✓ Total folders scanned: {validation_report['total_folders_found']}")
    print(f"✓ Valid candidates found: {validation_report['valid_folders_scanned']}")
    print(f"✓ Unique simulations processed: {len(all_data)}")
    print(f"ℹ️  Old versions suppressed: {validation_report['versions_suppressed']}")
    print(f"✗ Skipped folders (errors): {validation_report['skipped_folders']}")
    
    if validation_report['issues']:
        print(f"\nIssues found ({len(validation_report['issues'])}):")
        for folder_path, issue in validation_report['issues']:
            # Extract just the parent path for context
            path_obj = Path(folder_path)
            display_name = f".../{path_obj.parent.name}/{path_obj.name}"
            print(f"  ⚠️  {display_name}: {issue}")
    print("-" * 100)

    # Apply optional data manipulations (e.g., NG/G ratios)
    derived_entries, manipulation_reports = apply_data_manipulations(all_data, _DATA_MANIPULATIONS, _VALUE_MAPPINGS)
    if derived_entries:
        all_data.update(derived_entries)

    if manipulation_reports:
        print("\n" + "-" * 100)
        print("DATA MANIPULATIONS")
        print("-" * 100)
        for report in manipulation_reports:
            note = report.get('note')
            if note:
                print(f"  ⚠️  {report['name']}: {note}")
            else:
                print(f"  • {report['name']}: created {report['created']} derived series (missing pairs: {report['missing_pairs']})")
        print("-" * 100)
    
    print(f"\n✓ Loaded data for {len(all_data)} configuration-AoA combinations:")
    for (config, aoa), data in sorted(list(all_data.items())[:5]):  # Show first 5
        print(f"  {config} @ {aoa}: {len(data['lift'])} points - {data['turbulence_model']}")
    if len(all_data) > 5:
        print(f"  ... and {len(all_data) - 5} more")
    
    # Export to text files
    processed_data_dir = _OUTPUT_DIR / "processed_data"
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    for (config, aoa), data in all_data.items():
        # Create AoA specific folder
        aoa_dir = processed_data_dir / aoa
        aoa_dir.mkdir(exist_ok=True)

        # Export lift
        export_force_data(
            aoa_dir / f"{config}_lift.txt", 
            data['lift'], 
            {**data, 'config': config, 'aoa': aoa}, 
            "Lift"
        )
        
        # Export drag
        export_force_data(
            aoa_dir / f"{config}_drag.txt", 
            data['drag'], 
            {**data, 'config': config, 'aoa': aoa}, 
            "Drag"
        )
    
    print(f"✓ Exported {len(all_data) * 2} text files to: {processed_data_dir}")
    
    # Create summary statistics text file
    config_name = _OUTPUT_DIR.name
    summary_file = _OUTPUT_DIR / f"SUMMARY_{config_name}.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write(f"DATA PROCESSING SUMMARY - Last {_NUM_ITERATIONS} Iterations\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Data Sources:\n")
        for src in _DATA_SOURCES:
            f.write(f"  - {src}\n")
        f.write(f"Output Directory: {_OUTPUT_DIR}\n")
        f.write(f"Extraction Method: {_CONFIG_EXTRACTION_METHOD}\n\n")
        f.write("=" * 100 + "\n\n")
        
        sorted_data = sorted(all_data.items(), key=lambda x: (get_simulation_family_name(x[0][0]), extract_aoa_number(x[0][1])))
        
        for (config, aoa), data in sorted_data:
            lift_last_n = data['lift'][-_NUM_ITERATIONS:] if len(data['lift']) >= _NUM_ITERATIONS else data['lift']
            drag_last_n = data['drag'][-_NUM_ITERATIONS:] if len(data['drag']) >= _NUM_ITERATIONS else data['drag']
            
            lift_mean, lift_cov = compute_statistics(lift_last_n) if lift_last_n else (0, 0)
            drag_mean, drag_cov = compute_statistics(drag_last_n) if drag_last_n else (0, 0)
            
            f.write(f"Configuration: {config}\n")
            f.write(f"  Turbulence Model: {data['turbulence_model']}\n")
            f.write(f"  Geometry: {data['geometry']}\n")
            f.write(f"  Mesh: {data['mesh']}\n")
            f.write(f"  Grid: {data['grid']}\n")
            f.write(f"  Angle of Attack: {aoa}\n")
            f.write(f"  Total Data Points: {len(data['lift'])}\n")
            f.write(f"  Points Used: {len(lift_last_n)}\n")
            f.write("-" * 100 + "\n")
            f.write(f"  Lift Mean:  {lift_mean:12.4f} N\n")
            f.write(f"  Lift COV:   {lift_cov:12.2f} %\n")
            f.write(f"  Drag Mean:  {drag_mean:12.4f} N\n")
            f.write(f"  Drag COV:   {drag_cov:12.2f} %\n")
            f.write("=" * 100 + "\n\n")
    
    print(f"✓ Summary statistics text file: {summary_file}")
    
    # ==================== PART 2: CONVERGENCE ANALYSIS (OPTIONAL) ====================
    convergence_results = {}
    
    if _RUN_CONVERGENCE:
        print("\n" + "=" * 100)
        print("PART 2: CONVERGENCE ANALYSIS")
        print("=" * 100)
        
        print(f"\nAnalyzing convergence for {len(all_data)} configurations...")
        print(f"Max trim: {_CONVERGENCE_MAX_TRIM * 100}% of data, Tests: {_CONVERGENCE_NUM_TESTS}")
        
        for idx, ((config, aoa), data) in enumerate(all_data.items(), 1):
            if len(data['lift']) < _CONVERGENCE_NUM_TESTS + 10 or len(data['drag']) < _CONVERGENCE_NUM_TESTS + 10:
                print(f"\n  [{idx}/{len(all_data)}] Skipping: {config} - {aoa} (Insufficient data points: {len(data['lift'])})")
                continue

            print(f"\n  [{idx}/{len(all_data)}] Analyzing: {config} - {aoa}")
            
            # Create convergence plots and analyze data
            lift_results, drag_results, plot_path = plot_convergence_analysis(
                config, aoa,
                data['lift'],
                data['drag'],
                _OUTPUT_DIR,
                _CONVERGENCE_MAX_TRIM,
                _CONVERGENCE_NUM_TESTS
            )
            
            convergence_results[(config, aoa)] = {
                'lift': lift_results,
                'drag': drag_results,
                'plot': plot_path
            }
            
            # Print optimization recommendations with confidence info
            print(f"    ✓ Plot saved: {plot_path}")
            
            # Lift recommendation
            if lift_results['trim_recommendation'] is not None:
                print(f"    ✓ Lift - {lift_results['trim_reason']}")
            else:
                print(f"    ⚠️  Lift - No clear recommendation")
                for warning in lift_results.get('warnings', []):
                    print(f"       {warning}")
            
            # Drag recommendation
            if drag_results['trim_recommendation'] is not None:
                print(f"    ✓ Drag - {drag_results['trim_reason']}")
            else:
                print(f"    ⚠️  Drag - No clear recommendation")
                for warning in drag_results.get('warnings', []):
                    print(f"       {warning}")

        # Create Summary Charts
        print("\n  Generating convergence summary plots...")
        plot_convergence_summary(convergence_results, all_data, _OUTPUT_DIR, comparison_mode=_COMPARISON_MODE)
        
        print(f"\n✓ Convergence analysis complete")
        
        # Export convergence analysis text file
        convergence_dir = _OUTPUT_DIR / "convergence_analysis"
        convergence_dir.mkdir(parents=True, exist_ok=True)
        
        convergence_text_file = convergence_dir / "Convergence_Analysis_Results.txt"
        
        with open(convergence_text_file, 'w') as f:
            f.write("CONVERGENCE ANALYSIS RESULTS\n")
            f.write("=" * 120 + "\n\n")
            
            sorted_convergence = sorted(convergence_results.items(), key=lambda x: (get_simulation_family_name(x[0][0]), extract_aoa_number(x[0][1])))
            
            for (config, aoa), results in sorted_convergence:
                lift_results = results['lift']
                drag_results = results['drag']
                
                lift_min_cov_idx = np.argmin(lift_results['cov'])
                drag_min_cov_idx = np.argmin(drag_results['cov'])
                
                f.write(f"Configuration: {config} | AoA: {aoa}\n")
                f.write(f"Total Iterations: {len(all_data[(config, aoa)]['lift'])}\n")
                f.write("-" * 120 + "\n\n")
                
                f.write("LIFT CONVERGENCE:\n")
                f.write(f"{'Iterations_Removed':<20} {'Iterations_Used':<20} {'Mean':<15} {'StdDev':<15} {'COV(%)':<10}\n")
                f.write("-" * 120 + "\n")
                for i in range(len(lift_results['iterations_removed'])):
                    marker = " <-- MIN COV" if i == lift_min_cov_idx else ""
                    f.write(f"{lift_results['iterations_removed'][i]:<20} "
                           f"{lift_results['iterations_used'][i]:<20} "
                           f"{lift_results['mean'][i]:<15.6f} "
                           f"{lift_results['std_dev'][i]:<15.6f} "
                           f"{lift_results['cov'][i]:<10.2f}{marker}\n")
                
                f.write("\n")
                
                f.write("DRAG CONVERGENCE:\n")
                f.write(f"{'Iterations_Removed':<20} {'Iterations_Used':<20} {'Mean':<15} {'StdDev':<15} {'COV(%)':<10}\n")
                f.write("-" * 120 + "\n")
                for i in range(len(drag_results['iterations_removed'])):
                    marker = " <-- MIN COV" if i == drag_min_cov_idx else ""
                    f.write(f"{drag_results['iterations_removed'][i]:<20} "
                           f"{drag_results['iterations_used'][i]:<20} "
                           f"{drag_results['mean'][i]:<15.6f} "
                           f"{drag_results['std_dev'][i]:<15.6f} "
                           f"{drag_results['cov'][i]:<10.2f}{marker}\n")
                
                f.write("\n" + "=" * 120 + "\n\n")
        
        print(f"✓ Convergence text file: {convergence_text_file}")
        
        # Export optimized data to text files
        postprocessed_dir = convergence_dir / "optimized_data"
        postprocessed_dir.mkdir(parents=True, exist_ok=True)
        
        for (config, aoa), conv_data in sorted_convergence:
            data = all_data[(config, aoa)]
            
            # Create AoA specific folder
            aoa_dir = postprocessed_dir / aoa
            aoa_dir.mkdir(exist_ok=True)

            lift_min_cov_idx = np.argmin(conv_data['lift']['cov'])
            drag_min_cov_idx = np.argmin(conv_data['drag']['cov'])
            
            optimal_lift_trim = conv_data['lift']['iterations_removed'][lift_min_cov_idx]
            optimal_drag_trim = conv_data['drag']['iterations_removed'][drag_min_cov_idx]
            optimal_trim = max(optimal_lift_trim, optimal_drag_trim)
            
            optimized_lift = data['lift'][optimal_trim:]
            optimized_drag = data['drag'][optimal_trim:]
            
            # Export optimized lift
            export_force_data(
                aoa_dir / f"{config}_lift_optimized.txt",
                optimized_lift,
                {**data, 'config': config, 'aoa': aoa},
                f"Optimized Lift (Trimmed {optimal_trim})"
            )
            
            # Export optimized drag
            export_force_data(
                aoa_dir / f"{config}_drag_optimized.txt",
                optimized_drag,
                {**data, 'config': config, 'aoa': aoa},
                f"Optimized Drag (Trimmed {optimal_trim})"
            )
        
        print(f"✓ Optimized data files: {postprocessed_dir}")
        print(f"  ({len(convergence_results) * 2} files created)")
    else:
        print("\n⚠ Skipping convergence analysis (RUN_CONVERGENCE_ANALYSIS = False)")
    
    # ==================== PART 3: EXCEL OUTPUTS ====================
    print("\n" + "=" * 100)
    print("PART 3: GENERATING EXCEL OUTPUTS")
    print("=" * 100)
    
    # Extract config name from OUTPUT_DIR
    config_name = _OUTPUT_DIR.name
    excel_file = _OUTPUT_DIR / f'SUMMARY_{config_name}.xlsx'
    
    # Create workbook
    from openpyxl import Workbook
    wb = Workbook()
    
    # Sheet 1: Data Summary
    print("\n  Creating sheet: Data Summary")
    create_data_summary_sheet(wb, all_data, _NUM_ITERATIONS, convergence_results)
    
    # Sheet 2: Turbulence Comparison
    # Sheet 2: Turbulence / Grid Comparison
    if _COMPARISON_MODE != 'default':
        print(f"  Creating sheet: {_COMPARISON_MODE.capitalize()} Comparison")
        create_turbulence_comparison_sheet(wb, all_data, _NUM_ITERATIONS, convergence_results, comparison_mode=_COMPARISON_MODE)
    else:
        print("  Skipping comparison sheet (Mode: default)")
    
    # Sheet 3: Coefficients
    print("  Creating sheet: Coefficients")
    create_coefficients_sheet(wb, all_data, _NUM_ITERATIONS, convergence_results, _Q_TIMES_A)
    
    version_sheet_created = False
    # Only use COMPARISON_CONFIGS if explicitly in 'version' mode
    # For 'default', 'turbulence', 'grid', 'expanded', we rely on their specific logic.
    should_run_version_comparison = (_COMPARISON_MODE == 'version')
    
    if should_run_version_comparison:
        print("  Creating sheet: Version_Comparison")
        version_sheet_created = create_version_comparison_sheet(
            wb,
            all_data,
            _COMPARISON_CONFIGS,
            _NUM_ITERATIONS,
            convergence_results,
            _Q_TIMES_A,
            comparison_mode=_COMPARISON_MODE
        )
        if not version_sheet_created:
            print("  ⚠ Version comparison sheet skipped (no valid pairs or multi-version families)")

    # Sheet 4: Optimized Statistics (if convergence was run)
    if convergence_results:
        print("  Creating sheet: Optimized_Statistics")
        create_optimized_statistics_sheet(wb, all_data, convergence_results, _NUM_ITERATIONS, _Q_TIMES_A)
    
    # Save workbook
    wb.save(excel_file)
    
    sheet_count = 3
    if convergence_results:
        sheet_count += 1
    if version_sheet_created:
        sheet_count += 1
    print(f"\n✓ Excel file created with {sheet_count} sheets")
    print(f"✓ Saved to: {excel_file}")
    
    # ==================== PART 4: COEFFICIENT GRAPHS ====================
    print("\n" + "=" * 100)
    print("PART 4: GENERATING COEFFICIENT GRAPHS")
    print("=" * 100)
    
    # Calculate coefficients
    print("\nCalculating coefficients...")
    coefficient_data = {}
    
    for (config, aoa), data in all_data.items():
        # Get optimized or fixed iteration data
        if convergence_results and (config, aoa) in convergence_results:
            conv = convergence_results[(config, aoa)]
            lift_min_cov_idx = np.argmin(conv['lift']['cov'])
            drag_min_cov_idx = np.argmin(conv['drag']['cov'])
            
            optimal_lift_trim = conv['lift']['iterations_removed'][lift_min_cov_idx]
            optimal_drag_trim = conv['drag']['iterations_removed'][drag_min_cov_idx]
            optimal_trim = max(optimal_lift_trim, optimal_drag_trim)
            
            lift_values = data['lift'][optimal_trim:]
            drag_values = data['drag'][optimal_trim:]
        else:
            lift_values = data['lift'][-_NUM_ITERATIONS:] if len(data['lift']) >= _NUM_ITERATIONS else data['lift']
            drag_values = data['drag'][-_NUM_ITERATIONS:] if len(data['drag']) >= _NUM_ITERATIONS else data['drag']
        
        lift_mean = np.mean(lift_values) if lift_values else 0
        drag_mean = np.mean(drag_values) if drag_values else 0
        lift_std = np.std(lift_values) if lift_values else 0
        drag_std = np.std(drag_values) if drag_values else 0
        
        C_L = lift_mean / _Q_TIMES_A if _Q_TIMES_A != 0 else 0
        C_D = drag_mean / _Q_TIMES_A if _Q_TIMES_A != 0 else 0
        C_L_std = lift_std / _Q_TIMES_A if _Q_TIMES_A != 0 else 0
        C_D_std = drag_std / _Q_TIMES_A if _Q_TIMES_A != 0 else 0
        
        coefficient_data[(config, aoa)] = {
            'turbulence_model': data['turbulence_model'],
            'aoa_degrees': extract_aoa_number(aoa),
            'grid': data.get('grid', 'Unknown'), # Pass grid status for expanded graphs
            'C_L': C_L,
            'C_D': C_D,
            'C_L_std': C_L_std,
            'C_D_std': C_D_std,
        }
    
    print(f"✓ Coefficients calculated for {len(coefficient_data)} configurations")
    
    # Create graphs
    print("\nGenerating graphs...")
    create_coefficient_graphs(all_data, coefficient_data, _OUTPUT_DIR, _POSITION_MAP, _VALUE_MAPPINGS, 
                              comparison_mode=_COMPARISON_MODE, max_cov_threshold=_GRAPH_MAX_COV)

    # Create Expanded Graphs (Efficiency Ratio)
    print("Generating expanded graphs...")
    create_expanded_graphs(coefficient_data, _OUTPUT_DIR, comparison_mode=_COMPARISON_MODE, max_cov_threshold=_GRAPH_MAX_COV)
    
    graphs_dir = _OUTPUT_DIR / "coefficient_graphs"
    print(f"\n✓ Graphs saved to: {graphs_dir}")
    print("✓ Organization: coefficient_graphs / turbulence_model / config /")
    print("✓ Each config contains: C_L_vs_AoA.png, C_D_vs_AoA.png, C_L_C_D_Combined.png")
    
    # ==================== PART 5: GENERATING EXPORTED PLOTS (Cp, Y+) ====================
    if _COMPARISON_MODE != 'default':
        print("\n⚠ Skipping Extra Plots (Cp, Y+, Cf) — not applicable in comparison mode.")
    else:
        print("\n" + "=" * 100)
        print("PART 5: GENERATING EXPORTED PLOTS (Cp, Y+)")
        print("=" * 100)
    
        plot_counts = {"Cp": 0, "Y+": 0, "Cf": 0}
    
        for (config, aoa), data in all_data.items():
            source_dir = data.get('source_dir')
            if not source_dir:
                continue
            
            print(f"\n  Searching for XY files: config={config}, aoa={aoa}")
            print(f"    source_dir: {source_dir}")
                
            # Search for .xy files in the source folder
            all_xy_files = list(source_dir.glob("*.xy"))
            print(f"    Found {len(all_xy_files)} .xy files in source_dir")
            
            # Also check 'Exported_Plots' subdir if it exists (common output location)
            exported_subdir = source_dir / "Exported_Plots"
            if exported_subdir.exists():
                all_xy_files.extend(list(exported_subdir.glob("*.xy")))
            
            # Check sibling 'y_plus_pressure_data' folder (next to AoA folders)
            sibling_xy_dir = source_dir.parent / "y_plus_pressure_data"
            if sibling_xy_dir.exists():
                sibling_files = list(sibling_xy_dir.glob("*.xy"))
                print(f"    Found {len(sibling_files)} .xy files in sibling y_plus_pressure_data/")
                all_xy_files.extend(sibling_files)
            else:
                print(f"    Sibling dir not found: {sibling_xy_dir}")
                
            # Also check explicit XY data folder if configured
            if _XY_DATA_SOURCE_DIR and _XY_DATA_SOURCE_DIR.exists():
                explicit_files = list(_XY_DATA_SOURCE_DIR.glob("*.xy"))
                print(f"    Found {len(explicit_files)} .xy files in XY_DATA_SOURCE_DIR")
                all_xy_files.extend(explicit_files)
            elif _XY_DATA_SOURCE_DIR:
                print(f"    WARNING: XY_DATA_SOURCE_DIR does not exist: {_XY_DATA_SOURCE_DIR}")
            
            # Deduplicate (sibling and explicit might overlap)
            all_xy_files = list(set(all_xy_files))
            print(f"    Total unique .xy files: {len(all_xy_files)}")
                
            # Robust filtering helper
            aoa_num = extract_aoa_number(aoa)
            
            def is_match(f):
                if config not in f.name:
                    return False
                remainder = f.name.replace(config, "")
                parts = remainder.replace('_', '.').replace('-', '.').split('.')
                return str(aoa_num) in parts

            # Filter for Cp and Y+
            cp_files = [f for f in all_xy_files if ('cp' in f.name.lower() or 'pressure' in f.name.lower()) and is_match(f)]
            yplus_files = [f for f in all_xy_files if ('yplus' in f.name.lower() or 'y-plus' in f.name.lower() or 'y_plus' in f.name.lower()) and is_match(f)]
            cf_files = [f for f in all_xy_files if ('skin' in f.name.lower() or 'friction' in f.name.lower()) and is_match(f)]
            
            if cp_files or yplus_files or cf_files:
                print(f"    Matched: {len(cp_files)} Cp, {len(yplus_files)} Y+, {len(cf_files)} Cf files")
                for f in cp_files: print(f"      Cp: {f.name}")
                for f in yplus_files: print(f"      Y+: {f.name}")
                for f in cf_files: print(f"      Cf: {f.name}")
            
            # Setup output directories
            base_plot_dir = _OUTPUT_DIR / "Extra_Plots"
            cp_out_dir = base_plot_dir / "pressure_coefficient" / data['turbulence_model'] / config
            yplus_out_dir = base_plot_dir / "y_plus" / data['turbulence_model'] / config
            cf_out_dir = base_plot_dir / "skin_friction" / data['turbulence_model'] / config
            
            # Process Cp Files
            for f in cp_files:
                # (Already filtered by is_match)
                cp_out_dir.mkdir(parents=True, exist_ok=True)
                df = read_fluent_xy(f)
                if not df.empty:
                    output_path = cp_out_dir / f"Cp_{config}_{aoa}.png"
                    plot_xy_series(
                        df, 
                        title=f"Pressure Coefficient - {config} - {aoa}",
                        xlabel="X Position (m)",
                        ylabel="Pressure Coefficient ($C_p$)",
                        output_path=output_path,
                        invert_y=True
                    )
                    plot_counts["Cp"] += 1
                    
            # Process Y+ Files
            for f in yplus_files:
                # (Already filtered by is_match)
                yplus_out_dir.mkdir(parents=True, exist_ok=True)
                df = read_fluent_xy(f)
                if not df.empty:
                    output_path = yplus_out_dir / f"Yplus_{config}_{aoa}.png"
                    plot_xy_series(
                        df,
                        title=f"Wall Y+ Distribution - {config} - {aoa}",
                        xlabel="X Position (m)",
                        ylabel="Wall Y+",
                        output_path=output_path,
                        invert_y=False
                    )
                    plot_counts["Y+"] += 1
                    
            # Process Cf Files
            for f in cf_files:
                # (Already filtered by is_match)
                cf_out_dir.mkdir(parents=True, exist_ok=True)
                df = read_fluent_xy(f)
                if not df.empty:
                    output_path = cf_out_dir / f"Cf_{config}_{aoa}.png"
                    plot_xy_series(
                        df,
                        title=f"Skin Friction Coefficient - {config} - {aoa}",
                        xlabel="X Position (m)",
                        ylabel="Skin Friction Coefficient ($C_f$)",
                        output_path=output_path,
                        invert_y=False
                    )
                    plot_counts["Cf"] += 1

        print(f"\n✓ Generated {plot_counts['Cp']} Cp, {plot_counts['Y+']} Y+, {plot_counts['Cf']} Cf plots")
        print(f"✓ Saved to: {_OUTPUT_DIR / 'Extra_Plots'}")    
    # ==================== FINAL SUMMARY ====================
    print("\n" + "=" * 100)
    print("WORKFLOW COMPLETE!")
    print("=" * 100)
    print(f"\nOutputs saved to: {_OUTPUT_DIR}")
    print(f"  ├── processed_data.pkl")
    if convergence_results:
        print(f"  ├── convergence_results.pkl")
    print(f"  ├── SUMMARY_Statistics.xlsx ({sheet_count} sheets)")
    print(f"  ├── processed_data/ ({len(all_data) * 2} text files)")
    print(f"  └── coefficient_graphs/ (organized by turbulence model)")
    print("\n✓ All processing complete!")


if __name__ == "__main__":
    main()
