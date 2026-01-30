"""
Configuration settings for CFD Data Processing.
"""

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
