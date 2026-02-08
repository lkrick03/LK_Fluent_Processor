import sys
from pathlib import Path
import numpy as np

# Add the script directory to path
sys.path.append(str(Path(r'c:\Users\lukek\OneDrive - Liberty University\Honors Thesis\Python\Data Processing')))

from cfd_functions import _plot_multi_series, ACADEMIC_COLORS, ACADEMIC_MARKERS

def test_plotting():
    print("Starting plotting verification...")
    output_dir = Path(r'c:\Users\lukek\OneDrive - Liberty University\Honors Thesis\Python\Data Processing\test_plots')
    output_dir.mkdir(exist_ok=True)
    
    # Mock data
    aoa = np.linspace(0, 15, 5)
    
    plot_items = []
    models = ['SST', 'RNG', 'RSM']
    
    for i, model in enumerate(models):
        cl = 0.1 * aoa + 0.5 + 0.1 * i
        cd = 0.01 + 0.001 * aoa**2 + 0.005 * i
        cl_std = cl * 0.05
        cd_std = cd * 0.05
        
        plot_items.append({
            'aoa': aoa,
            'C_L': cl,
            'C_D': cd,
            'C_L_std': cl_std,
            'C_D_std': cd_std,
            'style': {
                'label': model,
                'color': ACADEMIC_COLORS[i],
                'marker': ACADEMIC_MARKERS[i]
            }
        })
    
    # Test multi-series
    print("  Testing _plot_multi_series (Lift)...")
    _plot_multi_series(plot_items, 'C_L', 'Test Lift Coefficient', 'Lift Coefficient ($C_L$)', 
                       output_dir / 'test_lift.png', max_cov_threshold=5.0)
    
    # Create "bad" data with high COV to test filtering
    bad_items = []
    for i, model in enumerate(models):
        cl = 0.1 * aoa + 0.5 + 0.1 * i
        # Make the last point extremely noisy (COV > 50%)
        cl_std = cl * 0.02 # Normal 2% noise
        cl_std[-1] = cl[-1] * 0.6 # 60% noise at last point
        
        bad_items.append({
            'aoa': aoa,
            'C_L': cl,
            'C_L_std': cl_std,
            'style': {
                'label': model,
                'color': ACADEMIC_COLORS[i],
                'marker': ACADEMIC_MARKERS[i]
            }
        })
        
    print("  Testing _plot_multi_series (Lift - With Bad Data & Filtering)...")
    _plot_multi_series(bad_items, 'C_L', 'Test Lift (Bad Data Filtered)', 'Lift Coefficient ($C_L$)', 
                       output_dir / 'test_lift_filtered.png', max_cov_threshold=5.0)

    # Test folder structure simulation
    print("  Testing folder structure logic...")
    # Simulate single series plot
    single_dir = output_dir / "Single" / "Test_Model"
    single_dir.mkdir(parents=True, exist_ok=True)
    _plot_multi_series([plot_items[0]], 'C_L', 'Test Single Series', 'Lift Coefficient ($C_L$)', 
                       single_dir / 'test_single.png')
    
    print(f"Verification plots saved to: {output_dir}")

if __name__ == "__main__":
    test_plotting()
