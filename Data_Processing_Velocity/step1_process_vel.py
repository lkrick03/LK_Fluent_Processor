"""
CFD Data Processing - Step 1: Process and Analyze
=================================================
This script handles the heavy data parsing and convergence analysis.
It loads raw simulation data, calculates statistics, and saves the 
processed state to a .pkl file for fast graphing in Step 2.

Author: Luke Krick
Date: March 2026
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pickle

from mvel_functions import (
    load_drag_data, compute_statistics, extract_velocity_number,
    analyze_convergence, plot_convergence_analysis,
    apply_data_manipulations, get_simulation_family_name
)
from mvel_config import (
    POSITION_MAP, VALUE_MAPPINGS, COMPARISON_CONFIGS, DATA_MANIPULATIONS,
    NAMING_SCHEMAS, ACTIVE_SCHEMA, RUN_PRESETS
)

# ==================== CONFIGURATION (MIRRORS main_vel.py) ====================

ACTIVE_PRESET = "O_version_comp_1.2.1.6-7.NG"

if ACTIVE_PRESET and ACTIVE_PRESET in RUN_PRESETS:
    preset = RUN_PRESETS[ACTIVE_PRESET]
    print(f"Loading Configuration Preset: '{preset.get('name', ACTIVE_PRESET)}'")
    DATA_SOURCES = preset.get("data_sources", [])
    OUTPUT_DIR = preset.get("output_dir", Path("."))
    COMPARISON_MODE = preset.get("comparison_mode", "single")
    VELOCITY_FILTER = preset.get("velocity_filter", [])
else:
    print("Loading Manual Configuration (ACTIVE_PRESET is None or Invalid)")
    DATA_SOURCES = []
    OUTPUT_DIR = Path(".") / "Manual_Run_Output"  # Override in local_config.py via a preset
    COMPARISON_MODE = 'grid'
    VELOCITY_FILTER = []

CONFIG_EXTRACTION_METHOD = 'case_file'
NUM_ITERATIONS = 150
RUN_CONVERGENCE_ANALYSIS = True
CONVERGENCE_MAX_TRIM = 0.8
CONVERGENCE_NUM_TESTS = 20

# Constant Angle of Attack for Velocity Sweep
AOA_DEG = 0

def export_force_data(filepath, data, metadata, force_type):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Configuration: {metadata['config']} | Velocity: {metadata['Velocity']} | Turbulence: {metadata['turbulence_model']}\n")
        f.write(f"# Geometry: {metadata['geometry']} | Mesh: {metadata['mesh']} | Grid: {metadata['grid']}\n")
        f.write(f"# Total Points: {len(data)}\n#\n")
        np.savetxt(f, data, fmt='%.6f')

def merge_processed_states(pkl_paths, velocity_filter=None):
    """
    Load and merge multiple pipeline_state.pkl files from single-mode runs.
    
    Instead of reprocessing raw simulation data, this pulls already-processed
    results from existing .pkl files and combines them into a single merged
    state that Step 2 can consume for comparison graphs/tables.
    
    Args:
        pkl_paths: List of paths to pipeline_state.pkl files.
        velocity_filter: Optional list of velocity numbers to keep.
    
    Returns:
        Tuple of (merged_all_data, merged_convergence_results, source_configs)
    """
    merged_data = {}
    merged_convergence = {}
    source_configs = []
    
    for pkl_path in pkl_paths:
        pkl_path = Path(pkl_path)
        if not pkl_path.exists():
            print(f"  [WARNING] Processed source not found: {pkl_path}")
            continue
        
        with open(pkl_path, "rb") as f:
            state = pickle.load(f)
        
        source_configs.append(state.get('config', {}))
        
        # Merge all_data (key collisions = last wins, but shouldn't happen
        # if each pkl is from a different single-mode config)
        for key, value in state['all_data'].items():
            if key in merged_data:
                print(f"  [WARNING] Duplicate key {key} — overwriting with data from {pkl_path.parent.name}")
            merged_data[key] = value
        
        # Merge convergence_results
        for key, value in state.get('convergence_results', {}).items():
            merged_convergence[key] = value
        
        print(f"  [OK] Loaded {len(state['all_data'])} entries from {pkl_path.parent.name}")
    
    # Apply velocity filter if specified
    if velocity_filter:
        initial = len(merged_data)
        merged_data = {
            k: v for k, v in merged_data.items()
            if extract_velocity_number(k[1]) in velocity_filter
        }
        # Also filter convergence results to match
        merged_convergence = {
            k: v for k, v in merged_convergence.items()
            if k in merged_data
        }
        print(f"  Velocity filter applied: {initial} -> {len(merged_data)} entries")
    
    print(f"  Total merged: {len(merged_data)} simulation entries, {len(merged_convergence)} convergence results")
    return merged_data, merged_convergence, source_configs

def main(config=None):
    # Setup configuration dictionary (simulating GUI or manual settings)
    _config_dict = config
    if config:
        _DATA_SOURCES           = config.get("data_sources", [])
        _OUTPUT_DIR             = config["output_dir"]
        _CONFIG_EXTRACTION_METHOD = config.get("config_extraction_method", 'case_file')
        _COMPARISON_MODE        = config["comparison_mode"]
        _VELOCITY_FILTER        = config.get("velocity_filter")
        _NUM_ITERATIONS         = config.get("num_iterations", NUM_ITERATIONS)
        _RUN_CONVERGENCE        = config.get("run_convergence_analysis", RUN_CONVERGENCE_ANALYSIS)
        _CONVERGENCE_MAX_TRIM   = config.get("convergence_max_trim", CONVERGENCE_MAX_TRIM)
        _CONVERGENCE_NUM_TESTS  = config.get("convergence_num_tests", CONVERGENCE_NUM_TESTS)
        _PROCESSED_SOURCES      = config.get("processed_sources", [])
        from mvel_config import NAMING_SCHEMAS as _ALL_SCHEMAS
        _schema = config.get("active_schema", ACTIVE_SCHEMA)
        _POSITION_MAP           = _ALL_SCHEMAS[_schema]
        _VALUE_MAPPINGS         = VALUE_MAPPINGS
        _DATA_MANIPULATIONS     = DATA_MANIPULATIONS
    else:
        _DATA_SOURCES           = DATA_SOURCES
        _OUTPUT_DIR             = OUTPUT_DIR
        _CONFIG_EXTRACTION_METHOD = CONFIG_EXTRACTION_METHOD
        _COMPARISON_MODE        = COMPARISON_MODE
        _VELOCITY_FILTER        = VELOCITY_FILTER
        _NUM_ITERATIONS         = NUM_ITERATIONS
        _RUN_CONVERGENCE        = RUN_CONVERGENCE_ANALYSIS
        _CONVERGENCE_MAX_TRIM   = CONVERGENCE_MAX_TRIM
        _CONVERGENCE_NUM_TESTS  = CONVERGENCE_NUM_TESTS
        _POSITION_MAP           = POSITION_MAP
        _VALUE_MAPPINGS         = VALUE_MAPPINGS
        _DATA_MANIPULATIONS     = DATA_MANIPULATIONS
        # Check module-level preset for processed_sources
        _PROCESSED_SOURCES = []
        if ACTIVE_PRESET and ACTIVE_PRESET in RUN_PRESETS:
            _PROCESSED_SOURCES = RUN_PRESETS[ACTIVE_PRESET].get("processed_sources", [])

    # ==================== MERGE PATH (from existing .pkl files) ====================
    # If processed_sources is set, skip all raw data loading and merge from pkl files.
    # This is used by comparison presets that pull from already-processed single runs.
    if _PROCESSED_SOURCES:
        print("=" * 100)
        print("STEP 1: MERGING PROCESSED DATA (from existing .pkl files)")
        print("=" * 100)
        print(f"  Comparison Mode: {_COMPARISON_MODE}")
        print(f"  Sources: {len(_PROCESSED_SOURCES)} .pkl files")
        for src in _PROCESSED_SOURCES:
            print(f"    - {src}")
        print()
        
        all_data, convergence_results, source_configs = merge_processed_states(
            _PROCESSED_SOURCES, _VELOCITY_FILTER
        )
        
        if not all_data:
            print("[ERROR] No data loaded from any processed source. Aborting.")
            return
        
        # Build merged config, inheriting num_iterations from first source
        _inherited_num_iters = source_configs[0].get('num_iterations', _NUM_ITERATIONS) if source_configs else _NUM_ITERATIONS
        _inherited_aoa = source_configs[0].get('aoa_deg', AOA_DEG) if source_configs else AOA_DEG
        
        state = {
            'all_data': all_data,
            'convergence_results': convergence_results,
            'config': {
                'output_dir': _OUTPUT_DIR,
                'comparison_mode': _COMPARISON_MODE,
                'num_iterations': _inherited_num_iters,
                'aoa_deg': _inherited_aoa,
                'merged_from': [str(p) for p in _PROCESSED_SOURCES],
            }
        }
        
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        state_file = _OUTPUT_DIR / "pipeline_state.pkl"
        with open(state_file, "wb") as f:
            pickle.dump(state, f)
        
        print("\n" + "=" * 100)
        print("STEP 1 COMPLETE! (Merged from processed sources)")
        print(f"  Merged {len(all_data)} simulation entries from {len(_PROCESSED_SOURCES)} sources")
        print(f"  State saved to: {state_file}")
        print("  You can now run step2_generate_outputs_vel.py to generate comparison outputs.")
        print("=" * 100)
        return

    # ==================== STANDARD PATH (raw data processing) ====================
    print("=" * 100)
    print("STEP 1: LOADING AND PROCESSING DATA")
    print("=" * 100)
    
    # 1. Load Data
    all_data, validation_report = load_drag_data(_DATA_SOURCES, _CONFIG_EXTRACTION_METHOD, _POSITION_MAP, _VALUE_MAPPINGS, comparison_mode=_COMPARISON_MODE)
    
    # 2. Filter via Velocity
    if _VELOCITY_FILTER:
        print(f"\nApplying Velocity Filter: {_VELOCITY_FILTER}")
        initial_count = len(all_data)
        filtered_data = {}
        for key, value in all_data.items():
            if extract_velocity_number(key[1]) in _VELOCITY_FILTER:
                 filtered_data[key] = value
        all_data = filtered_data
        print(f"   -> Filtered down to {len(all_data)} simulations (removed {initial_count - len(all_data)})")

    # 3. Apply Data Manipulations
    derived_entries, manipulation_reports = apply_data_manipulations(all_data, _DATA_MANIPULATIONS, _VALUE_MAPPINGS)
    if derived_entries:
        all_data.update(derived_entries)

    # Export Processed Text Files
    processed_data_dir = _OUTPUT_DIR / "processed_data"
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    for (config_id, Velocity), data in all_data.items():
        Velocity_dir = processed_data_dir / str(Velocity)
        Velocity_dir.mkdir(exist_ok=True)
        export_force_data(Velocity_dir / f"{config_id}_drag.txt", data['drag'], {**data, 'config': config_id, 'Velocity': Velocity}, "Drag")

    # 4. Convergence Analysis
    convergence_results = {}
    if _RUN_CONVERGENCE:
        print("\n" + "=" * 100)
        print("CONVERGENCE ANALYSIS")
        print("=" * 100)
        
        for idx, ((config_id, Velocity), data) in enumerate(all_data.items(), 1):
            if len(data['drag']) < _CONVERGENCE_NUM_TESTS + 10:
                print(f"  [{idx}/{len(all_data)}] Skipping: {config_id} - {Velocity} (Insufficient data points)")
                continue

            print(f"  [{idx}/{len(all_data)}] Analyzing: {config_id} - {Velocity}")
            # Note: We pass AOA_DEG to function but plot labels will say 'Velocity'
            drag_results, plot_path = plot_convergence_analysis(
                config_id, Velocity, data['drag'], _OUTPUT_DIR, _CONVERGENCE_MAX_TRIM, _CONVERGENCE_NUM_TESTS
            )
            convergence_results[(config_id, Velocity)] = {'lift': drag_results, 'drag': drag_results, 'plot': plot_path}

        
        # Export Optimized Data Text Files
        convergence_dir = _OUTPUT_DIR / "convergence_analysis"
        postprocessed_dir = convergence_dir / "optimized_data"
        postprocessed_dir.mkdir(parents=True, exist_ok=True)
        
        for (config_id, Velocity), conv_data in convergence_results.items():
            data = all_data[(config_id, Velocity)]
            Velocity_dir = postprocessed_dir / str(Velocity)
            Velocity_dir.mkdir(exist_ok=True)

            drag_min_cov_idx = np.argmin(conv_data['drag']['cov'])
            optimal_trim = conv_data['drag']['iterations_removed'][drag_min_cov_idx]
            
            export_force_data(Velocity_dir / f"{config_id}_drag.txt", data['drag'], {**data, 'config': config_id, 'Velocity': Velocity}, "Drag")
            
    # ==================== SAVE STATE WITH PICKLE ====================
    state = {
        'all_data': all_data,
        'convergence_results': convergence_results,
        'config': _config_dict if config else {
            'output_dir': _OUTPUT_DIR,
            'comparison_mode': _COMPARISON_MODE,
            'num_iterations': _NUM_ITERATIONS,
            'aoa_deg': AOA_DEG
        }
    }
    
    state_file = _OUTPUT_DIR / "pipeline_state.pkl"
    with open(state_file, "wb") as f:
        pickle.dump(state, f)
        
    print("\n" + "=" * 100)
    print("STEP 1 COMPLETE!")
    print(f"State saved to: {state_file}")
    print("You can now run step2_generate_outputs_vel.py to quickly graph this data.")
    print("=" * 100)

if __name__ == "__main__":
    main()
