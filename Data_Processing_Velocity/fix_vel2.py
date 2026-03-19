import os
import re
from pathlib import Path

base_dir = Path(r"C:\Users\lukek\OneDrive - Liberty University\Group-F.L.U.I.D. Research - GRID-FINS - GRID-FINS\Python\Data_Processing_Velocity")
f3 = base_dir / "mvel_functions.py"
content = f3.read_text(encoding="utf-8")

# validate_velocity_folder updates
content = re.sub(r"        - lift_file \(str\): Validated lift filename \(None if invalid\)\n", "", content)
content = re.sub(r"    # Find lift files\n    lift_candidates = \[f for f in filenames if 'lift_force' in f and f.endswith\('\.txt'\)\]\n    lift_file, lift_err = pick_best_file\(lift_candidates, \"lift_force_\*\.txt\"\)\n    if lift_err: errors\.append\(lift_err\)\n    \n", "", content)
content = re.sub(r"return is_valid, lift_file, drag_file, case_file, error_msg", "return is_valid, None, drag_file, case_file, error_msg", content)

# load_and_correct_forces -> load_and_correct_drag
content = re.sub(r"def load_and_correct_forces\(lift_file, drag_file, velocity_degrees\):\n.*?return true_lift\.tolist\(\), true_drag\.tolist\(\)",
"""def load_and_correct_drag(drag_file):
    \"\"\"Loads drag force data.\"\"\"
    drag_data = np.array(_read_force_file(drag_file))
    return drag_data.tolist()""", content, flags=re.DOTALL)

# load_lift_drag_data -> load_drag_data
content = content.replace("def load_lift_drag_data", "def load_drag_data")
content = content.replace("'lift_file': lift_file,", "")
content = re.sub(r"'lift': \[\], ", "", content)

# Function call to load_and_correct_drag
content = re.sub(r"        try:\n            lift_data, drag_data = load_and_correct_forces\(\n                winner\['dirpath'\] / winner\['lift_file'\], \n                winner\['dirpath'\] / winner\['drag_file'\], \n                winner\['metadata'\]\['velocity_number'\]\n            \)", 
"""        try:
            drag_data = load_and_correct_drag(
                winner['dirpath'] / winner['drag_file']
            )""", content, flags=re.DOTALL)

content = re.sub(r"            data_by_config_velocity\[key\]\['lift'\]\.extend\(lift_data\)\n", "", content)

# There might be references in docstrings or plotting for lift.
content = content.replace("lift and drag", "drag")

# Remove lift from plot_convergence_analysis
content = re.sub(r"def plot_convergence_analysis\(config_id, run_velocity, lift_data, drag_data, output_dir, max_trim=0\.8, num_tests=20\):",
                 r"def plot_convergence_analysis(config_id, run_velocity, drag_data, output_dir, max_trim=0.8, num_tests=20):", content)

content = re.sub(r"    lift_opt = optimize_trim_cov\(lift_data, max_trim, num_tests\)\n", "", content)

content = re.sub(r"    optimal_trim = max\(lift_opt\['optimal_trim'\], drag_opt\['optimal_trim'\]\)",
                 r"    optimal_trim = drag_opt['optimal_trim']", content)
                 
content = re.sub(r"    lift_trimmed = lift_data\[optimal_trim:\]\n", "", content)
content = re.sub(r"    lift_cov = \(np\.std\(lift_trimmed\) / np\.abs\(np\.mean\(lift_trimmed\)\)\) \* 100 if np\.mean\(lift_trimmed\) != 0 else 0\n", "", content)

content = re.sub(r"    fig, \(ax1, ax2\) = plt\.subplots\(2, 1, figsize=\(12, 12\)\)", 
                 r"    fig, ax2 = plt.subplots(1, 1, figsize=(12, 6))", content)

content = re.sub(r"    # --- LIFT PLOT ---\n.*?# --- DRAG PLOT ---", r"    # --- DRAG PLOT ---", content, flags=re.DOTALL)

content = re.sub(r"    return lift_opt, drag_opt, plot_path", r"    return drag_opt, plot_path", content)

content = re.sub(r"        lift_tests = conv_data\['lift'\]\['iterations_removed'\]\n        lift_cov = conv_data\['lift'\]\['cov'\]\n", "", content)
content = re.sub(r"        ax1\.plot\(lift_tests, lift_cov, 'o-', alpha=0\.6, label=label\)", "", content)

# Removing lift from create_data_summary_sheet
content = re.sub(r"        ws\.append\(\[\n            'Config', 'Velocity', 'Turbulence', 'Geometry', 'Mesh', 'Grid', 'Version',\n            'CL \(Mean\)', 'CL \(StdDev\)', 'CL \(CoV %\)',\n            'CD \(Mean\)', 'CD \(StdDev\)', 'CD \(CoV %\)'\n        \]\)",
r"""        ws.append([
            'Config', 'Velocity', 'Turbulence', 'Geometry', 'Mesh', 'Grid', 'Version',
            'CD (Mean)', 'CD (StdDev)', 'CD (CoV %)'
        ])""", content)

content = re.sub(r"            lift = data\['lift'\]\[-num_iterations:\]\n            lift_mean = np\.mean\(lift\)\n            lift_std = np\.std\(lift\)\n            lift_cov = \(lift_std / np\.abs\(lift_mean\)\) \* 100 if lift_mean != 0 else 0\n", "", content)
content = re.sub(r"            row = \[\n                config, velocity,\n                data\.get\('turbulence_model', 'N/A'\),\n                data\.get\('geometry', 'N/A'\),\n                data\.get\('mesh', 'N/A'\),\n                data\.get\('grid', 'N/A'\),\n                data\.get\('version', 'N/A'\),\n                lift_mean, lift_std, lift_cov,\n                drag_mean, drag_std, drag_cov\n            \]",
r"""            row = [
                config, velocity,
                data.get('turbulence_model', 'N/A'),
                data.get('geometry', 'N/A'),
                data.get('mesh', 'N/A'),
                data.get('grid', 'N/A'),
                data.get('version', 'N/A'),
                drag_mean, drag_std, drag_cov
            ]""", content)


f3.write_text(content, encoding="utf-8")
print("mvel_functions.py updated.")
