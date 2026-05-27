target1 = """        _plot_multi_series(plot_items, 'Ratio', 
                           f'{family} - Efficiency Improvement', 
                           'Efficiency Ratio ($(C_L/C_D)_G / (C_L/C_D)_{NG}$)',
                           grid_dir / "Efficiency_Ratio_vs_velocity.png",
                           max_cov_threshold=max_cov_threshold)"""

target2 = """            _plot_multi_series(
                combined_items, 'Ratio',
                'All Families — Efficiency Improvement',
                'Efficiency Ratio ($(C_L/C_D)_G / (C_L/C_D)_{NG}$)',
                combined_dir / "Combined_Efficiency_Ratio_vs_velocity.png",
                max_cov_threshold=max_cov_threshold
            )"""

target3 = """    _plot_dual_axis_cl_cd(plot_items, output_dir, title_prefix, max_cov_threshold, reference_data=reference_data)"""

with open('mvel_functions.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(target1, "")
content = content.replace(target2, "")
content = content.replace(target3, "")

with open('mvel_functions.py', 'w', encoding='utf-8') as f:
    f.write(content)

import py_compile
py_compile.compile('mvel_functions.py')
