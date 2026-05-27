"""
Configuration settings for CFD Data Processing.
"""

from pathlib import Path

# Naming Schemas: Define how to parse different config string formats
# Each schema maps field names to their position (0-indexed after splitting by '.')
# Set 'grid' to None if your naming convention doesn't include a grid suffix

NAMING_SCHEMAS = {
    # For configs like: 4.3.1.3.NG (5 parts with grid suffix)
    '5-part': {
        'velocity': 0,       # Index 0: Velocity number
        'mesh': 1,           # Index 1: Mesh number
        'turbulence': 2,     # Index 2: Turbulence model number
        'version': 3,        # Index 3: Version number
        'grid': 4,           # Index 4: Grid type (NG/G)
    },
    # For configs like: 4.3.1.2 (4 parts, no grid suffix)
    '4-part': {
        'velocity': 0,       # Index 0: Velocity number
        'mesh': 1,           # Index 1: Mesh number
        'turbulence': 2,     # Index 2: Turbulence model number
        'version': 3,        # Index 3: Version number
        'grid': None,        # No grid field in this format
    },
}

# Select which schema to use based on your data format
ACTIVE_SCHEMA = '5-part'  # Change to '5-part' for configs like 4.3.1.3.NG

# Legacy alias for backward compatibility
POSITION_MAP = NAMING_SCHEMAS[ACTIVE_SCHEMA]

# Value Mappings
VALUE_MAPPINGS = {
    'velocity': {
        4: '24.38',
        5: '14.3773',
    },
    'mesh': {
        1: 'OLD',
        2: 'OLD',
        3: 'Y+ 30',
        4: 'Adapted',
        5: 'Unstrucutred',
        6: 'Y+ 5'
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
        'NG': 'No Grid',
        'G': 'With Grid',
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
# for every AoA within the same geometry/mesh/turbulence/version grouping.
DATA_MANIPULATIONS = [
    {
        'name': 'NG_div_G',
        'enabled': False,          # Set True to activate
        'group_by': ['geometry', 'mesh', 'turbulence_model', 'version', 'aoa'],
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
    "single_4.3.1.G": {
        "name": "4.3.1.G Single Run",
        "data_sources": [
            Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.1.3.G"),
            Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.1.4.G"),
            Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.1.5.G"),
            Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.1.6.G"),     
        ],
        "output_dir": Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.4\4.3\4.3.1\4.3.1.G"),
        "comparison_mode": "single",
        "aoa_filter": []
    },

    "single_4.3.2.NG": {
        "name": "4.3.2.NG Single Run",
        "data_sources": [
            Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.2.1.NG"),
        ],
        "output_dir": Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Singular_Data\2414.6.4\4.3\4.3.2\4.3.2.1.NG"),
        "comparison_mode": "single",
        "aoa_filter": []
    }
        #"turbulence_4.3": {
        #"name": "4.3 Turbulence Comparison",
        #"data_sources": [
            #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.1.4.NG"),
            #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.2.4.NG"),
            #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.3.4.NG"),
            #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.1.4.G"),
            #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.2.4.G"),
            #Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\2414_006_004.3\4.3.3.4.G"),
        #],
        #"output_dir": Path(r"C:\Users\lukek\OneDrive\Documents\Thesis\NACA_2414_2D\Fluent\Directories\Processed_Data\Comparisons\2414.6.4.3\Turbulence_comp"),
        #"comparison_mode": "turbulence",
        #"aoa_filter": [0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,11,11.5,12,12.5,13,13.5,14,14.5,15,15.5,16,16.5,17,17.5,18,18.5,19,19.5,20]
    #}
}
