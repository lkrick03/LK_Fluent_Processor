"""
Configuration settings for CFD Data Processing (Velocity-Based).
"""

from pathlib import Path

# Naming Schemas: Define how to parse different config string formats
# Each schema maps field names to their position (0-indexed after splitting by '.')
# Set 'grid' to None if your naming convention doesn't include a grid suffix

NAMING_SCHEMAS = {
    # For configs like: 4.3.1.3.NG (5 parts with grid suffix)
    '5-part': {
        'aoa': 0,            # Index 0: AoA number (SWAPPED from velocity)
        'mesh': 1,           # Index 1: Mesh number
        'turbulence': 2,     # Index 2: Turbulence model number
        'version': 3,        # Index 3: Version number
        'grid': 4,           # Index 4: Grid type (NG/G)
    },
    # For configs like: 4.3.1.2 (4 parts, no grid suffix)
    '4-part': {
        'aoa': 0,            # Index 0: AoA number (SWAPPED from velocity)
        'mesh': 1,           # Index 1: Mesh number
        'turbulence': 2,     # Index 2: Turbulence model number
        'version': 3,        # Index 3: Version number
        'grid': None,        # No grid field in this format
    },
}

# Select which schema to use based on your data format
ACTIVE_SCHEMA = '5-part'  # Change to '5-part' for configs like 4.3.1.3.NG

# Specify whether Drag should be inverted (multiply by -1)
INVERT_DRAG_SIGN = False    

# Legacy alias for backward compatibility
POSITION_MAP = NAMING_SCHEMAS[ACTIVE_SCHEMA]

# Value Mappings
VALUE_MAPPINGS = {
    'aoa': {                 # SWAPPED from velocity
        1: '0',
        2: '5',
        3: '10',
        4: '15',
        5: '20'
    },
    'mesh': {
        1: '4V6',
        2: '4-inch-half-fin',
        3: '4-inch-full-fin',
        4: '6-inch-third-fin',
        5: '6-inch-half-fin',
        6: '6-inch-full-fin'
    },
    'turbulence': {
        1: 'SST',
        2: 'K-Epsilon Standard',
        3: 'RSM',
    },
    'version': {
        1: 'V1',
        2: 'V2',
        3: 'V3',
        4: 'V4',
        5: 'V5',
        6: 'Single_Precision',
        7: 'Double_Precision',
    },
    'grid': {
        'NG': 'No Brake',
        'G': 'With Brake',
    }
}

# Comparison Configurations
# Provide the configurations you want to compare for each base setup.
# When a list is supplied, the first entry is treated as the baseline and
# every subsequent entry is compared directly against it.
COMPARISON_CONFIGS = {
    '4.3.NG': [
        '4.3.1.4.NG',  # Baseline (e.g., original run)
        '4.3.2.4.NG',  # Compared against the baseline
    ],
}

# Derived Data Manipulations
# Each entry defines how to create a synthetic data series using existing inputs.
# Example below (disabled) would divide No-Grid (NG) results by With-Grid (G) results
# for every Velocity within the same geometry/mesh/turbulence/version grouping.
DATA_MANIPULATIONS = [
    {
        'name': 'NG_div_G',
        'enabled': False,          # Set True to activate
        'group_by': ['geometry', 'mesh', 'turbulence_model', 'version', 'velocity'],  # SWAPPED aoa to velocity
        'numerator_grid': 'NG',    # Accepts either shorthand (NG/G) or descriptive ('No Grid')
        'denominator_grid': 'G',
        'operation': 'divide',     # Supported: divide, subtract, percent_difference
        'output_suffix': 'NG_div_G',
        'output_grid_label': 'NG/G Ratio',
        'description': 'Creates NG/G force ratios for each matching simulation family.'
    }
]

# Preset Registry
# Define custom runs with predefined data sources, output directory, and comparison modes.
# Set ACTIVE_PRESET in main.py to the key of the preset you want to run, or None to use manual settings.
#
# For SINGLE-mode presets: use "data_sources" to point at raw unprocessed_data directories.
# For COMPARISON-mode presets: use "processed_sources" to point at pipeline_state.pkl files
#   from already-processed single runs. This avoids reprocessing raw data — Step 1 will
#   merge the existing .pkl files and Step 2 generates comparison outputs from the merge.

RUN_PRESETS = {
    "T_single_1.1.1.2.G": {
        "name": "1.1.1.2.G Single Run (Velocity)",
        "data_sources": [
            r"C:\Users\lukek\Documents\Rocketry_CFD\TRINITY\directories\unprocessed_data\1.1.1.2.G",
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\TRINITY\directories\processed_data\1.1.1.2.G"),
        "comparison_mode": "single",
        "velocity_filter": []  # SWAPPED from aoa_filter
    },
    "O_single_1.2.1.2.NG": {
        "name": "1.2.1.2.NG Single Run (Velocity)",
        "data_sources": [
            r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\unprocessed_data\1.2.1.2.NG",
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.2.NG"),
        "comparison_mode": "single",
        "velocity_filter": []  # SWAPPED from aoa_filter
    },
    "O_single_1.2.1.2.G": { #This needs to be adjusted
        "name": "1.2.1.2.G Single Run (Velocity)",
        "data_sources": [
            r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\Setup_Jou\HPC\1.2.1.2.NG_setup",
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\Setup_Jou\HPC\1.2.1.2.NG_setup"),
        "comparison_mode": "single",
        "velocity_filter": []  # SWAPPED from aoa_filter
    },
    "O_single_1.2.1.6.NG": {
        "name": "1.2.1.6.NG Single Run (Velocity)",
        "data_sources": [
            r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\unprocessed_data\1.2.1.6.NG",
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.6.NG"),
        "comparison_mode": "single",
        "velocity_filter": []  # SWAPPED from aoa_filter
    },
    "O_single_1.2.1.7.NG": {
        "name": "1.2.1.7.NG Single Run (Velocity)",
        "data_sources": [
            r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\unprocessed_data\1.2.1.7.NG",
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.7.NG"),
        "comparison_mode": "single",
        "velocity_filter": []  # SWAPPED from aoa_filter
    },
    "O_single_1.2.1.8.NG": {
        "name": "1.2.1.8.NG Single Run (Velocity)",
        "data_sources": [
            r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\unprocessed_data\1.2.1.8.NG",
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.8.NG"),
        "comparison_mode": "single",
        "velocity_filter": []  # SWAPPED from aoa_filter
    },

    # ---- SINGLE PRESET TEMPLATE ----
    # Uncomment and adjust. Replace <ROCKET> with project name (e.g. OMEGA),
    # and <CONFIG> with the config string (e.g. 1.2.1.8.NG).
    #
    # "<ROCKET>_single_<CONFIG>": {
    #     "name": "<CONFIG> Single Run (Velocity)",
    #     "data_sources": [
    #         r"C:\Users\lukek\Documents\Rocketry_CFD\<ROCKET>\directories\unprocessed_data\<CONFIG>",
    #     ],
    #     "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\<ROCKET>\directories\processed_data\<CONFIG>"),
    #     "comparison_mode": "single",
    #     "velocity_filter": []
    # },

    # ---- COMPARISON PRESETS (merge from processed .pkl files) ----


    "O_version_comp_1.2.1.6-7.NG": {
        "name": "1.2.1.6-7.NG Version Comparison (Velocity)",
        "processed_sources": [
            Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.6.NG\pipeline_state.pkl"),
            Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.7.NG\pipeline_state.pkl"),
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.6-7.NG"),
        "comparison_mode": "version",
        "velocity_filter": []  # SWAPPED from aoa_filter
    },

    # ---- COMPARISON PRESET TEMPLATE ----
    # Uncomment and adjust paths to use.
    #
    # "compare_grid_1.2.1.2": {
    #     "name": "Grid Comparison: 1.2.1.2 NG vs G",
    #     "processed_sources": [
    #         Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.2.NG\pipeline_state.pkl"),
    #         Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\1.2.1.2.G\pipeline_state.pkl"),
    #     ],
    #     "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\OMEGA\directories\processed_data\Comparisons\1.2.1.2_Grid"),
    #     "comparison_mode": "grid",
    #     "velocity_filter": []
    # },
}

