"""
Configuration settings for CFD Data Processing.
"""

# Naming Schemas: Define how to parse different config string formats
# Each schema maps field names to their position (0-indexed after splitting by '.')
# Set 'grid' to None if your naming convention doesn't include a grid suffix

NAMING_SCHEMAS = {
    # For configs like: 4.3.1.3.NG (5 parts with grid suffix)
    '5-part': {
        'geometry': 0,       # Index 0: Geometry number
        'mesh': 1,           # Index 1: Mesh number
        'turbulence': 2,     # Index 2: Turbulence model number
        'version': 3,        # Index 3: Version number
        'grid': 4,           # Index 4: Grid type (NG/G)
    },
    # For configs like: 4.3.1.2 (4 parts, no grid suffix)
    '4-part': {
        'geometry': 0,       # Index 0: Geometry number
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
    'geometry': {
        3: '2414_006_003',
        4: '2414_006_004',
    },
    'mesh': {
        1: 'OLD',
        2: 'OLD',
        3: 'Medium',
        4: 'Adapted',
        5: 'Unstrucutred',
        6: 'Fine'
    },
    'turbulence': {
        1: 'K-Omega SST',
        2: 'K-Epsilon Standard',
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
