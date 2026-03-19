import os
from pathlib import Path

def process_file_exact(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Exact strings to replace where AOA was used as an iterator or dictionary key
    replacements = [
        ("(config, AOA)", "(config, Velocity)"),
        ("AOA_dir", "Velocity_dir"),
        ("\"AOA_", "\"Velocity_"),
        ("'AOA'", "'Velocity'"),
        ("AOA_str", "Velocity_str"),
        ("AOA_num", "Velocity_num"),
        ("AOA_dict", "Velocity_dict"),
        ("{AOA}", "{Velocity}"),
        ("AOA:", "Velocity:"),
        ("AOA_degrees", "Velocity_value"),
        ("C_L_vs_AOA", "C_L_vs_Velocity"),
        ("C_D_vs_AOA", "C_D_vs_Velocity"),
        ("extract_velocity_number(AOA)", "extract_velocity_number(Velocity)")
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

folder = Path(r"c:\Users\lukek\OneDrive - Liberty University\Group-F.L.U.I.D. Research - GRID-FINS - GRID-FINS\Python\Data_Processing_Velocity")
process_file_exact(folder / "main_vel.py")
process_file_exact(folder / "mvel_functions.py")

print("Exact replacement complete.")
