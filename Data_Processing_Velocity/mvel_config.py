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
INVERT_DRAG_SIGN = True

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
        6: 'V6',
        7: 'V7',
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

RUN_PRESETS = {
    "single_1.1.1.2.G": {
        "name": "1.1.1.2.G Single Run (Velocity)",
        "data_sources": [
            r"C:\Users\lukek\Documents\Rocketry_CFD\TRINITY\directories\unprocessed_data\1.1.1.2.G",
        ],
        "output_dir": Path(r"C:\Users\lukek\Documents\Rocketry_CFD\TRINITY\directories\processed_data\1.1.1.2.G"),
        "comparison_mode": "single",
        "velocity_filter": []  # SWAPPED from aoa_filter
    }
}
