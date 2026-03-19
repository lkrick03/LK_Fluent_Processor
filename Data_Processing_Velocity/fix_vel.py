import os
from pathlib import Path

base_dir = Path(r"C:\Users\lukek\OneDrive - Liberty University\Group-F.L.U.I.D. Research - GRID-FINS - GRID-FINS\Python\Data_Processing_Velocity")

# 1. Update step1_process_vel.py
f1 = base_dir / "step1_process_vel.py"
content = f1.read_text(encoding="utf-8")
content = content.replace("load_lift_drag_data", "load_drag_data")
content = content.replace("all_data, validation_report = load_drag_data", "all_data, validation_report = load_drag_data")

# Modify lines 123-124 to only export drag
new_export = """        export_force_data(Velocity_dir / f"{config_id}_drag.txt", data['drag'], {**data, 'config': config_id, 'Velocity': Velocity}, "Drag")"""
import re
content = re.sub(r"        export_force_data.*?lift.*?\n.*?export_force_data.*?drag.*?\n", new_export + "\n", content, flags=re.MULTILINE)

content = re.sub(r"if len\(data\['lift'\]\) < _CONVERGENCE_NUM_TESTS \+ 10 or len\(data\['drag'\]\) < _CONVERGENCE_NUM_TESTS \+ 10:",
                 r"if len(data['drag']) < _CONVERGENCE_NUM_TESTS + 10:", content)

content = re.sub(r"lift_results, drag_results, plot_path = plot_convergence_analysis\(",
                 r"drag_results, plot_path = plot_convergence_analysis(", content)
                 
content = re.sub(r"config_id, Velocity, data\['lift'\], data\['drag'\], _OUTPUT_DIR, _CONVERGENCE_MAX_TRIM, _CONVERGENCE_NUM_TESTS",
                 r"config_id, Velocity, data['drag'], _OUTPUT_DIR, _CONVERGENCE_MAX_TRIM, _CONVERGENCE_NUM_TESTS", content)
                 
content = re.sub(r"convergence_results\[\(config_id, Velocity\)\] = \{'lift': lift_results, 'drag': drag_results, 'plot': plot_path\}",
                 r"convergence_results[(config_id, Velocity)] = {'drag': drag_results, 'plot': plot_path}", content)

content = re.sub(r"            lift_min_cov_idx = np\.argmin\(conv_data\['lift'\]\['cov'\]\)\n", "", content)
content = re.sub(r"            drag_min_cov_idx = np\.argmin\(conv_data\['drag'\]\['cov'\]\)\n",
                 r"            drag_min_cov_idx = np.argmin(conv_data['drag']['cov'])\n", content)
content = re.sub(r"            optimal_trim = max\(conv_data\['lift'\]\['iterations_removed'\]\[lift_min_cov_idx\], conv_data\['drag'\]\['iterations_removed'\]\[drag_min_cov_idx\]\)\n",
                 r"            optimal_trim = conv_data['drag']['iterations_removed'][drag_min_cov_idx]\n", content)

content = re.sub(r"            export_force_data\(Velocity_dir / f\"{config_id}_lift_optimized\.txt\".*?\n", "", content)

f1.write_text(content, encoding="utf-8")
print("step1_process_vel.py updated.")

# 2. Update step2_generate_outputs_vel.py
f2 = base_dir / "step2_generate_outputs_vel.py"
content = f2.read_text(encoding="utf-8")

content = re.sub(r"            lift_min_cov_idx = np\.argmin\(conv\['lift'\]\['cov'\]\)\n", "", content)
content = re.sub(r"            drag_min_cov_idx = np\.argmin\(conv\['drag'\]\['cov'\]\)\n",
                 r"            drag_min_cov_idx = np.argmin(conv['drag']['cov'])\n", content)
content = re.sub(r"            optimal_trim = max\(conv\['lift'\]\['iterations_removed'\]\[lift_min_cov_idx\], conv\['drag'\]\['iterations_removed'\]\[drag_min_cov_idx\]\)\n",
                 r"            optimal_trim = conv['drag']['iterations_removed'][drag_min_cov_idx]\n", content)

content = re.sub(r"            lift_values = data\['lift'\]\[optimal_trim:\]\n", "", content)
content = re.sub(r"            lift_values = data\['lift'\]\[-_NUM_ITERATIONS:\] if len\(data\['lift'\]\) >= _NUM_ITERATIONS else data\['lift'\]\n", "", content)

content = re.sub(r"        C_L = \(np\.mean\(lift_values\) / _Q_TIMES_A\) if lift_values and _Q_TIMES_A else 0\n", "", content)
content = re.sub(r"            'C_L': C_L,\n", "", content)
content = re.sub(r"            'C_L_std': \(np\.std\(lift_values\) / _Q_TIMES_A\) if lift_values and _Q_TIMES_A else 0,\n", "", content)

f2.write_text(content, encoding="utf-8")
print("step2_generate_outputs_vel.py updated.")
