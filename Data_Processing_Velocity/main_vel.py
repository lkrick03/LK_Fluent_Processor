"""
CFD Data Processing - Consolidated Pipeline
===========================================
This is a wrapper script to run both Step 1 (Processing) 
and Step 2 (Generating Outputs) in a single execution.

Author: Luke Krick
Date: March 2026
"""

from step1_process_vel import main as run_step1
from step2_generate_outputs_vel import main as run_step2
from mvel_config import RUN_PRESETS

ACTIVE_PRESET = "single_1.1.1.2.G"

def main():
    print("=" * 100)
    print("CFD DATA PROCESSING - FULL PIPELINE (VELOCITY)")
    print("=" * 100)
    
    # Optional: If you wanted to run a specific configuration preset instead of letting the default constants take over.
    # config = RUN_PRESETS[ACTIVE_PRESET]
    # run_step1(config=config)
    # run_step2(config=config)
    
    # Run Defaults
    run_step1()
    run_step2()
    
    print("\n" * 2)
    print("*" * 50)
    print("PIPELINE FULLY COMPLETE!")
    print("*" * 50)

if __name__ == "__main__":
    main()
