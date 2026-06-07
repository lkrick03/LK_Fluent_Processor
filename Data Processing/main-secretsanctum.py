"""
CFD Data Processing - Main Execution Script
Consolidates all 4 notebooks into a single executable workflow.

This script:
1. Loads and processes CFD simulation data
2. (Optional) Runs convergence analysis
3. Generates Excel summary files
4. Creates coefficient graphs

Author: [Your Name]
Date: December 2025
"""

import os
import numpy as np
import pandas as pd
import pickle
from cfd_functions import (
    load_lift_drag_data, compute_statistics, extract_aoa_number,
    analyze_convergence, plot_convergence_analysis, create_data_summary_sheet, create_turbulence_comparison_sheet,
    create_version_comparison_sheet, create_coefficients_sheet, create_optimized_statistics_sheet, apply_excel_formatting,
    create_coefficient_graphs
)


# ==================== USER CONFIGURATION ====================

# Input/Output Directories
BASE_PATH = r"."  # Update to your data directory
OUTPUT_DIR = r"."  # Update to your output directory

# Configuration Extraction Method
CONFIG_EXTRACTION_METHOD = 'case_file'  # Options: 'case_file' or 'folder'

# Position Mapping (0-indexed for config parts split by '.')
# For config '4.3.1.3.NG': [0]=4 (geom), [1]=3 (mesh), [2]=1 (turb), [3]=3 (ver), [4]=NG (grid)
POSITION_MAP = {
    'geometry': 0,       # Index 0: Geometry number
    'mesh': 1,           # Index 1: Mesh number
    'turbulence': 2,     # Index 2: Turbulence model number
    'version': 3,        # Index 3: Version number
    'grid': 4,           # Index 4: Grid type
}

# Value Mappings
VALUE_MAPPINGS = {
    'geometry': {
        3: '2414_006_003',
        4: '2414_006_004',
    },
    'mesh': {
        1: 'Coarse',
        2: 'Medium',
        3: 'Baseline',
        4: 'ExtraFine',
        5: 'Ultra',
    },
    'turbulence': {
        1: 'SST',
        2: 'RNG',
        3: 'RSM',
    },
    'version': {
        1: 'V1',
        2: 'V2',
        3: 'V3',
    },
    'grid': {
        'NG': 'No Grid',
        'G': 'With Grid',
    }
}

# Comparison Configurations
COMPARISON_CONFIGS = {
    '4.3.NG': ['4.3.1.NG', '4.3.2.NG', '4.3.3.NG'],
}

# Processing Parameters
NUM_ITERATIONS = 150  # Number of last iterations to use for statistics
RUN_CONVERGENCE_ANALYSIS = True  # Set to False to skip convergence analysis
CONVERGENCE_MAX_TRIM = 0.8  # Maximum fraction of data to trim (0.8 = 80%)
CONVERGENCE_NUM_TESTS = 20  # Number of trim amounts to test

# Coefficient Calculation Parameters
SPAN = 0.85344
CHORD = 0.1
AIR_DENSITY = 1.225
VELOCITY = 24.38

REFERENCE_AREA = SPAN * CHORD
DYNAMIC_PRESSURE = 0.5 * AIR_DENSITY * VELOCITY**2
Q_TIMES_A = DYNAMIC_PRESSURE * REFERENCE_AREA

# ==================== MAIN WORKFLOW ====================

def main():
    """Main execution function."""
    
    print("=" * 100)
    print("CFD DATA PROCESSING - CONSOLIDATED WORKFLOW")
    print("=" * 100)
    
    # ==================== PART 1: LOAD AND PROCESS DATA ====================
    print("\n" + "=" * 100)
    print("PART 1: LOADING AND PROCESSING DATA")
    print("=" * 100)
    
    print(f"\nLoading data from: {BASE_PATH}")
    all_data, validation_report = load_lift_drag_data(BASE_PATH, CONFIG_EXTRACTION_METHOD, POSITION_MAP, VALUE_MAPPINGS)
    
    # Print validation report
    print("\n" + "-" * 100)
    print("DATA VALIDATION REPORT")
    print("-" * 100)
    print(f"✓ Total AoA folders scanned: {validation_report['total_aoa_folders']}")
    print(f"✓ Valid AoA folders loaded: {validation_report['valid_aoa_folders']}")
    print(f"✗ Skipped AoA folders: {validation_report['skipped_aoa_folders']}")
    
    if validation_report['issues']:
        print(f"\nIssues found ({len(validation_report['issues'])}):")
        for folder_path, issue in validation_report['issues']:
            # Extract just the AoA folder name for readability
            aoa_folder = os.path.basename(folder_path)
            print(f"  ⚠️  {aoa_folder}: {issue}")
    print("-" * 100)
    
    print(f"\n✓ Loaded data for {len(all_data)} configuration-AoA combinations:")
    for (config, aoa), data in sorted(list(all_data.items())[:5]):  # Show first 5
        print(f"  {config} @ {aoa}: {len(data['lift'])} points - {data['turbulence_model']}")
    if len(all_data) > 5:
        print(f"  ... and {len(all_data) - 5} more")
    
    # Save processed data (include validation report)
    pickle_file = os.path.join(OUTPUT_DIR, 'processed_data.pkl')
    with open(pickle_file, 'wb') as f:
        pickle.dump({
            'all_data': dict(all_data),
            'validation_report': validation_report,
            'config_info': {
                'POSITION_MAP': POSITION_MAP,
                'VALUE_MAPPINGS': VALUE_MAPPINGS,
                'COMPARISON_CONFIGS': COMPARISON_CONFIGS,
                'CONFIG_EXTRACTION_METHOD': CONFIG_EXTRACTION_METHOD,
            },
            'paths': {
                'base_path': BASE_PATH,
                'output_dir': OUTPUT_DIR,
            }
        }, f)
    
    print(f"\n✓ Data saved to: {pickle_file}")
    print(f"  File size: {os.path.getsize(pickle_file) / 1024:.1f} KB")
    
    # Export to text files
    processed_data_dir = os.path.join(OUTPUT_DIR, "processed_data")
    os.makedirs(processed_data_dir, exist_ok=True)
    
    for (config, aoa), data in all_data.items():
        # Export lift
        with open(os.path.join(processed_data_dir, f"{config}_lift.txt"), 'w', encoding='utf-8') as f:
            f.write(f"# Configuration: {config} | AoA: {aoa} | Turbulence: {data['turbulence_model']}\n")
            f.write(f"# Geometry: {data['geometry']} | Mesh: {data['mesh']} | Grid: {data['grid']}\n")
            f.write(f"# Total Points: {len(data['lift'])}\n#\n")
            for value in data['lift']:
                f.write(f"{value}\n")
        
        # Export drag
        with open(os.path.join(processed_data_dir, f"{config}_drag.txt"), 'w', encoding='utf-8') as f:
            f.write(f"# Configuration: {config} | AoA: {aoa} | Turbulence: {data['turbulence_model']}\n")
            f.write(f"# Geometry: {data['geometry']} | Mesh: {data['mesh']} | Grid: {data['grid']}\n")
            f.write(f"# Total Points: {len(data['drag'])}\n#\n")
            for value in data['drag']:
                f.write(f"{value}\n")
    
    print(f"✓ Exported {len(all_data) * 2} text files to: {processed_data_dir}")
    
    # Create summary statistics text file
    config_name = os.path.basename(BASE_PATH.rstrip(os.sep))
    summary_file = os.path.join(OUTPUT_DIR, f"SUMMARY_{config_name}.txt")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write(f"DATA PROCESSING SUMMARY - Last {NUM_ITERATIONS} Iterations\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Base Path: {BASE_PATH}\n")
        f.write(f"Output Directory: {OUTPUT_DIR}\n")
        f.write(f"Extraction Method: {CONFIG_EXTRACTION_METHOD}\n\n")
        f.write("=" * 100 + "\n\n")
        
        sorted_data = sorted(all_data.items(), key=lambda x: (x[0][0], extract_aoa_number(x[0][1])))
        
        for (config, aoa), data in sorted_data:
            lift_last_n = data['lift'][-NUM_ITERATIONS:] if len(data['lift']) >= NUM_ITERATIONS else data['lift']
            drag_last_n = data['drag'][-NUM_ITERATIONS:] if len(data['drag']) >= NUM_ITERATIONS else data['drag']
            
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
    
    if RUN_CONVERGENCE_ANALYSIS:
        print("\n" + "=" * 100)
        print("PART 2: CONVERGENCE ANALYSIS")
        print("=" * 100)
        
        print(f"\nAnalyzing convergence for {len(all_data)} configurations...")
        print(f"Max trim: {CONVERGENCE_MAX_TRIM * 100}% of data, Tests: {CONVERGENCE_NUM_TESTS}")
        
        for idx, ((config, aoa), data) in enumerate(all_data.items(), 1):
            print(f"\n  [{idx}/{len(all_data)}] Analyzing: {config} - {aoa}")
            
            # Create convergence plots and analyze data
            lift_results, drag_results, plot_path = plot_convergence_analysis(
                config, aoa,
                data['lift'],
                data['drag'],
                OUTPUT_DIR,
                CONVERGENCE_MAX_TRIM,
                CONVERGENCE_NUM_TESTS
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

        
        # Save convergence results
        conv_pickle = os.path.join(OUTPUT_DIR, 'convergence_results.pkl')
        with open(conv_pickle, 'wb') as f:
            pickle.dump({
                'convergence_results': convergence_results,
                'num_iterations': NUM_ITERATIONS,
                'max_trim': CONVERGENCE_MAX_TRIM,
                'num_tests': CONVERGENCE_NUM_TESTS
            }, f)
        
        print(f"\n✓ Convergence analysis complete")
        print(f"✓ Results saved to: {conv_pickle}")
        
        # Export convergence analysis text file
        convergence_dir = os.path.join(OUTPUT_DIR, "convergence_analysis")
        os.makedirs(convergence_dir, exist_ok=True)
        
        convergence_text_file = os.path.join(convergence_dir, "Convergence_Analysis_Results.txt")
        
        with open(convergence_text_file, 'w') as f:
            f.write("=" * 120 + "\n")
            f.write("CONVERGENCE ANALYSIS RESULTS\n")
            f.write("=" * 120 + "\n\n")
            
            for (config, aoa), conv_data in convergence_results.items():
                lift_results = conv_data['lift']
                drag_results = conv_data['drag']
                
                lift_min_cov_idx = np.argmin(lift_results['cov'])
                drag_min_cov_idx = np.argmin(drag_results['cov'])
                
                f.write(f"Configuration: {config}\n")
                f.write(f"Angle of Attack: {aoa}\n")
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
        postprocessed_dir = os.path.join(convergence_dir, "optimized_data")
        os.makedirs(postprocessed_dir, exist_ok=True)
        
        for (config, aoa), conv_data in convergence_results.items():
            data = all_data[(config, aoa)]
            
            lift_min_cov_idx = np.argmin(conv_data['lift']['cov'])
            drag_min_cov_idx = np.argmin(conv_data['drag']['cov'])
            
            optimal_lift_trim = conv_data['lift']['iterations_removed'][lift_min_cov_idx]
            optimal_drag_trim = conv_data['drag']['iterations_removed'][drag_min_cov_idx]
            optimal_trim = max(optimal_lift_trim, optimal_drag_trim)
            
            optimized_lift = data['lift'][optimal_trim:]
            optimized_drag = data['drag'][optimal_trim:]
            
            # Export optimized lift
            with open(os.path.join(postprocessed_dir, f"{config}_lift_optimized.txt"), 'w') as f:
                f.write(f"# Optimized Lift Data for {config}\n")
                f.write(f"# Trimmed {optimal_trim} iterations from start\n")
                f.write(f"# Using {len(optimized_lift)} iterations\n")
                f.write(f"# Mean: {np.mean(optimized_lift):.6f} N\n")
                f.write(f"# Std Dev: {np.std(optimized_lift):.6f} N\n")
                f.write(f"# COV: {(np.std(optimized_lift)/np.mean(optimized_lift)*100):.2f} %\n#\n")
                for value in optimized_lift:
                    f.write(f"{value}\n")
            
            # Export optimized drag
            with open(os.path.join(postprocessed_dir, f"{config}_drag_optimized.txt"), 'w') as f:
                f.write(f"# Optimized Drag Data for {config}\n")
                f.write(f"# Trimmed {optimal_trim} iterations from start\n")
                f.write(f"# Using {len(optimized_drag)} iterations\n")
                f.write(f"# Mean: {np.mean(optimized_drag):.6f} N\n")
                f.write(f"# Std Dev: {np.std(optimized_drag):.6f} N\n")
                f.write(f"# COV: {(np.std(optimized_drag)/np.mean(optimized_drag)*100):.2f} %\n#\n")
                for value in optimized_drag:
                    f.write(f"{value}\n")
        
        print(f"✓ Optimized data files: {postprocessed_dir}")
        print(f"  ({len(convergence_results) * 2} files created)")
    else:
        print("\n⚠ Skipping convergence analysis (RUN_CONVERGENCE_ANALYSIS = False)")
    
    # ==================== PART 3: EXCEL OUTPUTS ====================
    print("\n" + "=" * 100)
    print("PART 3: GENERATING EXCEL OUTPUTS")
    print("=" * 100)
    
    # Extract config name from BASE_PATH (last folder name)
    config_name = os.path.basename(BASE_PATH.rstrip(os.sep))
    excel_file = os.path.join(OUTPUT_DIR, f'SUMMARY_{config_name}.xlsx')
    
    # Create workbook
    from openpyxl import Workbook
    wb = Workbook()
    
    # Sheet 1: Data Summary
    print("\n  Creating sheet: Data Summary")
    create_data_summary_sheet(wb, all_data, NUM_ITERATIONS, convergence_results)
    
    # Sheet 2: Turbulence Comparison
    print("  Creating sheet: Turbulence_Comparison")
    create_turbulence_comparison_sheet(wb, all_data, NUM_ITERATIONS, convergence_results)
    
    # Sheet 3: Coefficients
    print("  Creating sheet: Coefficients")
    create_coefficients_sheet(wb, all_data, NUM_ITERATIONS, convergence_results, Q_TIMES_A)
    
    version_sheet_created = False
    if COMPARISON_CONFIGS:
        print("  Creating sheet: Version_Comparison")
        version_sheet_created = create_version_comparison_sheet(
            wb,
            all_data,
            COMPARISON_CONFIGS,
            NUM_ITERATIONS,
            convergence_results,
            Q_TIMES_A,
        )
        if not version_sheet_created:
            print("  ⚠ Version comparison sheet skipped (no valid pairs)")

    # Sheet 4: Optimized Statistics (if convergence was run)
    if convergence_results:
        print("  Creating sheet: Optimized_Statistics")
        create_optimized_statistics_sheet(wb, all_data, convergence_results, NUM_ITERATIONS, Q_TIMES_A)
    
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
            lift_values = data['lift'][-NUM_ITERATIONS:] if len(data['lift']) >= NUM_ITERATIONS else data['lift']
            drag_values = data['drag'][-NUM_ITERATIONS:] if len(data['drag']) >= NUM_ITERATIONS else data['drag']
        
        lift_mean = np.mean(lift_values) if lift_values else 0
        drag_mean = np.mean(drag_values) if drag_values else 0
        lift_std = np.std(lift_values) if lift_values else 0
        drag_std = np.std(drag_values) if drag_values else 0
        
        C_L = lift_mean / Q_TIMES_A if Q_TIMES_A != 0 else 0
        C_D = drag_mean / Q_TIMES_A if Q_TIMES_A != 0 else 0
        C_L_std = lift_std / Q_TIMES_A if Q_TIMES_A != 0 else 0
        C_D_std = drag_std / Q_TIMES_A if Q_TIMES_A != 0 else 0
        
        coefficient_data[(config, aoa)] = {
            'turbulence_model': data['turbulence_model'],
            'aoa_degrees': extract_aoa_number(aoa),
            'C_L': C_L,
            'C_D': C_D,
            'C_L_std': C_L_std,
            'C_D_std': C_D_std,
        }
    
    print(f"✓ Coefficients calculated for {len(coefficient_data)} configurations")
    
    # Create graphs
    print("\nGenerating graphs...")
    create_coefficient_graphs(all_data, coefficient_data, OUTPUT_DIR, POSITION_MAP, VALUE_MAPPINGS)
    
    graphs_dir = os.path.join(OUTPUT_DIR, "coefficient_graphs")
    print(f"\n✓ Graphs saved to: {graphs_dir}")
    print("✓ Organization: coefficient_graphs / turbulence_model / config /")
    print("✓ Each config contains: C_L_vs_AoA.png, C_D_vs_AoA.png, C_L_C_D_Combined.png")
    
    # ==================== FINAL SUMMARY ====================
    print("\n" + "=" * 100)
    print("WORKFLOW COMPLETE!")
    print("=" * 100)
    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print(f"  ├── processed_data.pkl")
    if convergence_results:
        print(f"  ├── convergence_results.pkl")
    print(f"  ├── SUMMARY_Statistics.xlsx ({sheet_count} sheets)")
    print(f"  ├── processed_data/ ({len(all_data) * 2} text files)")
    print(f"  └── coefficient_graphs/ (organized by turbulence model)")
    print("\n✓ All processing complete!")


if __name__ == "__main__":
    main()
