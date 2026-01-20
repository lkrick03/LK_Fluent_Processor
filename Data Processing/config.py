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
COMPARISON_CONFIGS = {
    '4.3.NG': ['4.3.1.NG', '4.3.2.NG', '4.3.3.NG'],
}
