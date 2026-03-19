import re

with open('mvel_functions.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Apply Drag Inversion in load_drag_data
# We want to inject this right under `drag_data = load_and_correct_drag(...)`
# Let's find:
#             drag_data = load_and_correct_drag(
#                 winner['dirpath'] / winner['drag_file']
#             )
# And replace with:
#             drag_data = load_and_correct_drag(
#                 winner['dirpath'] / winner['drag_file']
#             )
#             
#             try:
#                 from mvel_config import INVERT_DRAG_SIGN
#                 if INVERT_DRAG_SIGN:
#                     drag_data = [-x for x in drag_data]
#             except ImportError:
#                 pass

old_load = """            drag_data = load_and_correct_drag(
                winner['dirpath'] / winner['drag_file']
            )"""

new_load = """            drag_data = load_and_correct_drag(
                winner['dirpath'] / winner['drag_file']
            )
            
            try:
                from mvel_config import INVERT_DRAG_SIGN
                if INVERT_DRAG_SIGN:
                    drag_data = [-x for x in drag_data]
            except ImportError:
                pass"""

text = text.replace(old_load, new_load)


# 2. Scrub "Lift Mean" and "Lift COV" blocks from the codebase.
# These usually look like:
# 'Lift Mean (N)'
# 'Lift COV (%)'
# Also the code that populates them.
# There are multiple tables created in sheets: Turbine Comparison, Version Comparison.
# Let's aggressively use regex to remove exact lines or blocks.

# Remove Table 1: Lift Mean (and Table 3: Lift COV) blocks in create_turbulence_comparison_sheet
# and similarly in other sheets.

# We will just remove any line that contains "Lift Mean" or "Lift COV"
# but wait, there are blocks of code calculating it like `lift_mean = ...`
# A brute force approach to remove all lines containing `lift_mean`, `lift_cov`, `Lift Mean`, `Lift COV`, `lift_std`

# regex to delete lines containing certain lift keys
lines = text.split('\n')
new_lines = []

skip_block = False
for line in lines:
    # If the line defines or uses lift statistics for Excel presentation, skip it.
    if ('Lift Mean' in line or 'Lift COV' in line or 'lift_mean' in line or 'lift_cov' in line or 'lift_std' in line):
        # Only delete if it's not a generic data prep thing that hasn't been cleaned up
        if 'ws.cell' in line or 'lift_' in line.lower() or 'Lift ' in line:
            continue
            
    # Also skip "Table 1: Lift Mean" comments
    if '# Table 1: Lift Mean' in line or '# Table 3: Lift COV' in line:
        continue
        
    # Remove 'Lift Mean (N)', 'Lift COV (%)', from columns lists
    if "columns = " in line and "'Lift Mean (N)'" in line:
        line = line.replace("'Lift Mean (N)', ", "")
        line = line.replace("'Lift COV (%)', ", "")
        
    new_lines.append(line)

text = '\n'.join(new_lines)


# 3. Clean up the polyfill at the end of load_drag_data
#     # Quick polyfill for lift data to prevent KeyErrors in step2 
#     for config_key in data_by_config_velocity:
#         if 'drag' in data_by_config_velocity[config_key]:
#             data_by_config_velocity[config_key]['lift'] = data_by_config_velocity[config_key]['drag'].copy()
polyfill = """    # Quick polyfill for lift data to prevent KeyErrors in step2 
    for config_key in data_by_config_velocity:
        if 'drag' in data_by_config_velocity[config_key]:
            data_by_config_velocity[config_key]['lift'] = data_by_config_velocity[config_key]['drag'].copy()"""

text = text.replace(polyfill, "")

# Same thing for get_optimized_data where lift values were extracted.
# It returns lift_values, drag_values, but we may break unpackings if we just remove lift entirely there without updating step1.
# Let's just write this to file and test.

with open('mvel_functions.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Scrubbed Lift from Excel sheets and applied INVERT_DRAG_SIGN.")
