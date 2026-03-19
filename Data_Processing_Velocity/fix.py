import sys

with open('mvel_functions.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix plot_convergence_analysis
old_func = """def plot_convergence_analysis(config, velocity, lift_data, drag_data, output_dir, max_trim, num_tests):
    \"\"\"
    Create convergence analysis plots showing how statistics change with data trimming.
    
    Args:
        config: Configuration string
        velocity: Velocity string
        lift_data: Array of lift force values
        drag_data: Array of drag force values
        output_dir: Directory to save plots
        max_trim: Maximum fraction of data to trim
        num_tests: Number of trim amounts to test
    
    Returns:
        Tuple of (lift_results, drag_results, plot_path)
    \"\"\"
    # Analyze both drag
    lift_results = analyze_convergence(np.array(lift_data), min_trim=0, max_trim=max_trim, num_tests=num_tests)
    drag_results = analyze_convergence(np.array(drag_data), min_trim=0, max_trim=max_trim, num_tests=num_tests)
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 9))
    
    # Plot 1: Lift Mean vs Iterations Removed
    ax1.plot(lift_results['iterations_removed'], lift_results['mean'], 'o-', linewidth=2, markersize=8, color='#1f77b4')
    ax1.set_xlabel('Iterations Removed from Start', fontsize=16)
    ax1.set_ylabel('Lift Mean (N)', fontsize=16)
    ax1.set_title(f'Lift Mean Convergence\\n{config} - {velocity}', fontweight='bold', fontsize=18)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Lift COV vs Iterations Removed
    ax2.plot(lift_results['iterations_removed'], lift_results['cov'], 'o-', linewidth=2, markersize=8, color='#ff7f0e')
    ax2.set_xlabel('Iterations Removed from Start', fontsize=16)
    ax2.set_ylabel('Lift COV (%)', fontsize=16)
    ax2.set_title(f'Lift COV Convergence\\n{config} - {velocity}', fontweight='bold', fontsize=18)
    ax2.grid(True, alpha=0.3)
    
    # Highlight minimum COV point for lift
    min_cov_idx = np.argmin(lift_results['cov'])
    ax2.axvline(x=lift_results['iterations_removed'][min_cov_idx], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax2.text(lift_results['iterations_removed'][min_cov_idx], max(lift_results['cov']), 
             f"  Min COV\\n  Remove: {lift_results['iterations_removed'][min_cov_idx]}\\n  Use: {lift_results['iterations_used'][min_cov_idx]}", 
             color='red', fontweight='bold', fontsize=13)
    
    # Plot 3: Drag Mean vs Iterations Removed
    ax3.plot(drag_results['iterations_removed'], drag_results['mean'], 'o-', linewidth=2, markersize=8, color='#2ca02c')
    ax3.set_xlabel('Iterations Removed from Start', fontsize=16)
    ax3.set_ylabel('Drag Mean (N)', fontsize=16)
    ax3.set_title(f'Drag Mean Convergence\\n{config} - {velocity}', fontweight='bold', fontsize=18)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Drag COV vs Iterations Removed
    ax4.plot(drag_results['iterations_removed'], drag_results['cov'], 'o-', linewidth=2, markersize=8, color='#d62728')
    ax4.set_xlabel('Iterations Removed from Start', fontsize=16)
    ax4.set_ylabel('Drag COV (%)', fontsize=16)
    ax4.set_title(f'Drag COV Convergence\\n{config} - {velocity}', fontweight='bold', fontsize=18)
    ax4.grid(True, alpha=0.3)
    
    # Highlight minimum COV point for drag
    min_cov_idx = np.argmin(drag_results['cov'])
    ax4.axvline(x=drag_results['iterations_removed'][min_cov_idx], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax4.text(drag_results['iterations_removed'][min_cov_idx], max(drag_results['cov']), 
             f"  Min COV\\n  Remove: {drag_results['iterations_removed'][min_cov_idx]}\\n  Use: {drag_results['iterations_used'][min_cov_idx]}", 
             color='red', fontweight='bold', fontsize=13)
    
    plt.tight_layout()
    
    # Save convergence analysis plot
    convergence_dir = output_dir / "convergence_analysis"
    convergence_dir.mkdir(parents=True, exist_ok=True)
    
    plot_file = convergence_dir / f"convergence_{config}_{velocity}.png"
    try:
        plt.savefig(plot_file, dpi=300) 
    except Exception as e:
        print(f"    ⚠️  Warning: Could not save plot {plot_file.name}: {e}")
    plt.close()
    
    return lift_results, drag_results, str(plot_file)"""

new_func = """def plot_convergence_analysis(config, velocity, drag_data, output_dir, max_trim, num_tests):
    \"\"\"
    Create convergence analysis plots showing how statistics change with data trimming.
    \"\"\"
    # Analyze drag
    drag_results = analyze_convergence(np.array(drag_data), min_trim=0, max_trim=max_trim, num_tests=num_tests)
    
    # Create figure with subplots
    fig, (ax3, ax4) = plt.subplots(1, 2, figsize=(16, 5))
    
    # Plot 3: Drag Mean vs Iterations Removed
    ax3.plot(drag_results['iterations_removed'], drag_results['mean'], 'o-', linewidth=2, markersize=8, color='#2ca02c')
    ax3.set_xlabel('Iterations Removed from Start', fontsize=16)
    ax3.set_ylabel('Drag Mean (N)', fontsize=16)
    ax3.set_title(f'Drag Mean Convergence\\n{config} - {velocity}', fontweight='bold', fontsize=18)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Drag COV vs Iterations Removed
    ax4.plot(drag_results['iterations_removed'], drag_results['cov'], 'o-', linewidth=2, markersize=8, color='#d62728')
    ax4.set_xlabel('Iterations Removed from Start', fontsize=16)
    ax4.set_ylabel('Drag COV (%)', fontsize=16)
    ax4.set_title(f'Drag COV Convergence\\n{config} - {velocity}', fontweight='bold', fontsize=18)
    ax4.grid(True, alpha=0.3)
    
    # Highlight minimum COV point for drag
    min_cov_idx = np.argmin(drag_results['cov'])
    ax4.axvline(x=drag_results['iterations_removed'][min_cov_idx], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax4.text(drag_results['iterations_removed'][min_cov_idx], max(drag_results['cov']), 
             f"  Min COV\\n  Remove: {drag_results['iterations_removed'][min_cov_idx]}\\n  Use: {drag_results['iterations_used'][min_cov_idx]}", 
             color='red', fontweight='bold', fontsize=13)
    
    plt.tight_layout()
    
    # Save convergence analysis plot
    convergence_dir = output_dir / "convergence_analysis"
    convergence_dir.mkdir(parents=True, exist_ok=True)
    
    plot_file = convergence_dir / f"convergence_{config}_{velocity}.png"
    try:
        plt.savefig(plot_file, dpi=300) 
    except Exception as e:
        print(f"    ⚠️  Warning: Could not save plot {plot_file.name}: {e}")
    plt.close()
    
    return drag_results, str(plot_file)"""

if old_func in text:
    text = text.replace(old_func, new_func)
    print("plot_convergence_analysis updated.")
else:
    print("plot_convergence_analysis old string not fully matched!")

# Also fix the `get_optimized_data` issues which cause KeyError: 'lift' if it doesn't exist.
text = text.replace("lift_min_cov_idx = np.argmin(conv['lift']['cov'])", "# lift_min_cov_idx = np.argmin(conv['lift']['cov'])")
text = text.replace("optimal_lift_trim = conv['lift']['iterations_removed'][lift_min_cov_idx]", "# optimal_lift_trim")
text = text.replace("optimal_trim = max(optimal_lift_trim, optimal_drag_trim)", "optimal_trim = optimal_drag_trim")

with open('mvel_functions.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Done")
