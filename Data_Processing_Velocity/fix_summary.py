import re

with open('mvel_functions.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix plot_convergence_summary to remove lift.
old_summary = """        # Extract metrics
        # Lift COV
        lift_cov_min_idx = np.argmin(results['lift']['cov'])
        lift_cov_min = results['lift']['cov'][lift_cov_min_idx]
        lift_trim_opt = results['lift']['iterations_removed'][lift_cov_min_idx]
        
        # Drag COV
        drag_cov_min_idx = np.argmin(results['drag']['cov'])
        drag_cov_min = results['drag']['cov'][drag_cov_min_idx]
        drag_trim_opt = results['drag']['iterations_removed'][drag_cov_min_idx]
        
        velocity_num = extract_velocity_number(velocity)
        
        summary_data[base_family][sim_type][velocity_num] = {
            'lift_cov': lift_cov_min,
            'lift_trim': lift_trim_opt,
            'drag_cov': drag_cov_min,
            'drag_trim': drag_trim_opt
        }"""
        
new_summary = """        # Extract metrics
        # Drag COV
        drag_cov_min_idx = np.argmin(results['drag']['cov'])
        drag_cov_min = results['drag']['cov'][drag_cov_min_idx]
        drag_trim_opt = results['drag']['iterations_removed'][drag_cov_min_idx]
        
        velocity_num = extract_velocity_number(velocity)
        
        summary_data[base_family][sim_type][velocity_num] = {
            'drag_cov': drag_cov_min,
            'drag_trim': drag_trim_opt
        }"""

if old_summary in text:
    text = text.replace(old_summary, new_summary)
else:
    print("WARNING: old_summary not found")

old_plot_setup = """        # Setup Figure: 2x2
        fig, axes = plt.subplots(2, 2, figsize=(16, 9))
        ((ax1, ax2), (ax3, ax4)) = axes"""

new_plot_setup = """        # Setup Figure: 1x2 (only drag)
        fig, axes = plt.subplots(1, 2, figsize=(16, 5))
        (ax2, ax4) = axes"""

if old_plot_setup in text:
    text = text.replace(old_plot_setup, new_plot_setup)
else:
    print("WARNING: old_plot_setup not found")
    
old_extract_arrays = """            l_cov = [sim_points[a]['lift_cov'] for a in velocitys]
            d_cov = [sim_points[a]['drag_cov'] for a in velocitys]
            l_trim = [sim_points[a]['lift_trim'] for a in velocitys]
            d_trim = [sim_points[a]['drag_trim'] for a in velocitys]
            
            # Plot
            line, = ax1.plot(velocitys, l_cov, linestyle='-', marker=marker, color=color, label=sim_type, alpha=0.8)
            ax2.plot(velocitys, d_cov, linestyle='-', marker=marker, color=color, label=sim_type, alpha=0.8)
            ax3.plot(velocitys, l_trim, linestyle='--', marker=marker, color=color, label=sim_type, alpha=0.8)
            ax4.plot(velocitys, d_trim, linestyle='--', marker=marker, color=color, label=sim_type, alpha=0.8)"""

new_extract_arrays = """            d_cov = [sim_points[a]['drag_cov'] for a in velocitys]
            d_trim = [sim_points[a]['drag_trim'] for a in velocitys]
            
            # Plot
            line, = ax2.plot(velocitys, d_cov, linestyle='-', marker=marker, color=color, label=sim_type, alpha=0.8)
            ax4.plot(velocitys, d_trim, linestyle='--', marker=marker, color=color, label=sim_type, alpha=0.8)"""

if old_extract_arrays in text:
    text = text.replace(old_extract_arrays, new_extract_arrays)
else:
    print("WARNING: old_extract_arrays not found")
    

old_labels = """        ax1.set_title(f'Lift COV vs velocity', fontweight='bold', fontsize=18)
        ax1.set_ylabel('Minimum COV (%)', fontsize=16)
        
        ax2.set_title(f'Drag COV vs velocity', fontweight='bold', fontsize=18)
        
        ax3.set_title(f'Lift Optimal Trim vs velocity', fontweight='bold', fontsize=18)
        ax3.set_xlabel('velocity (deg)', fontsize=16)
        ax3.set_ylabel('Iterations Removed', fontsize=16)
        
        ax4.set_title(f'Drag Optimal Trim vs velocity', fontweight='bold', fontsize=18)
        ax4.set_xlabel('velocity (deg)', fontsize=16)"""
        
new_labels = """        ax2.set_title(f'Drag COV vs velocity', fontweight='bold', fontsize=18)
        ax2.set_ylabel('Minimum COV (%)', fontsize=16)
        
        ax4.set_title(f'Drag Optimal Trim vs velocity', fontweight='bold', fontsize=18)
        ax4.set_xlabel('velocity (deg)', fontsize=16)
        ax4.set_ylabel('Iterations Removed', fontsize=16)"""

if old_labels in text:
    text = text.replace(old_labels, new_labels)
else:
    print("WARNING: old_labels not found")

# Replace velocity (deg) with Velocity string since velocity isn't in degrees
text = text.replace("Velocity (deg)", "Velocity")
text = text.replace("velocity (deg)", "Velocity")

with open('mvel_functions.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("plot_convergence_summary updated successfully.")
