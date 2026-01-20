# Data Validation System - Quick Test
# Run this to verify validation function works correctly

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cfd_functions import validate_aoa_folder

def test_validation_system():
    """Test the validation function with mock files"""
    
    print("="*80)
    print("DATA VALIDATION SYSTEM - TEST SUITE")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Valid folder (all files present)
        print("\n[Test 1] Valid folder with all files")
        print("-" * 80)
        valid_dir = os.path.join(tmpdir, "test_valid")
        os.makedirs(valid_dir, exist_ok=True)
        
        # Create test files
        Path(os.path.join(valid_dir, "lift_force_1.txt")).touch()
        Path(os.path.join(valid_dir, "drag_force_1.txt")).touch()
        Path(os.path.join(valid_dir, "case.cas.h5")).touch()
        
        filenames = os.listdir(valid_dir)
        is_valid, lift_file, drag_file, case_file, error_msg = validate_aoa_folder(valid_dir, filenames)
        
        print(f"is_valid: {is_valid}")
        print(f"lift_file: {lift_file}")
        print(f"drag_file: {drag_file}")
        print(f"case_file: {case_file}")
        print(f"error_msg: {error_msg}")
        assert is_valid == True, "Test 1 failed: should be valid"
        print("✓ Test 1 PASSED")
        
        # Test 2: Multiple lift files
        print("\n[Test 2] Multiple lift files (should fail)")
        print("-" * 80)
        dup_dir = os.path.join(tmpdir, "test_dup_lift")
        os.makedirs(dup_dir, exist_ok=True)
        
        Path(os.path.join(dup_dir, "lift_force_1.txt")).touch()
        Path(os.path.join(dup_dir, "lift_force_2.txt")).touch()
        Path(os.path.join(dup_dir, "drag_force_1.txt")).touch()
        Path(os.path.join(dup_dir, "case.cas.h5")).touch()
        
        filenames = os.listdir(dup_dir)
        is_valid, lift_file, drag_file, case_file, error_msg = validate_aoa_folder(dup_dir, filenames)
        
        print(f"is_valid: {is_valid}")
        print(f"error_msg: {error_msg}")
        assert is_valid == False, "Test 2 failed: should be invalid"
        assert "Multiple lift files" in error_msg, "Test 2 failed: error message should mention duplicates"
        print("✓ Test 2 PASSED")
        
        # Test 3: Missing case file
        print("\n[Test 3] Missing case file (should fail)")
        print("-" * 80)
        no_case_dir = os.path.join(tmpdir, "test_no_case")
        os.makedirs(no_case_dir, exist_ok=True)
        
        Path(os.path.join(no_case_dir, "lift_force_1.txt")).touch()
        Path(os.path.join(no_case_dir, "drag_force_1.txt")).touch()
        
        filenames = os.listdir(no_case_dir)
        is_valid, lift_file, drag_file, case_file, error_msg = validate_aoa_folder(no_case_dir, filenames)
        
        print(f"is_valid: {is_valid}")
        print(f"error_msg: {error_msg}")
        assert is_valid == False, "Test 3 failed: should be invalid"
        assert "No case file" in error_msg, "Test 3 failed: error message should mention missing case file"
        print("✓ Test 3 PASSED")
        
        # Test 4: Missing lift file
        print("\n[Test 4] Missing lift file (should fail)")
        print("-" * 80)
        no_lift_dir = os.path.join(tmpdir, "test_no_lift")
        os.makedirs(no_lift_dir, exist_ok=True)
        
        Path(os.path.join(no_lift_dir, "drag_force_1.txt")).touch()
        Path(os.path.join(no_lift_dir, "case.cas.h5")).touch()
        
        filenames = os.listdir(no_lift_dir)
        is_valid, lift_file, drag_file, case_file, error_msg = validate_aoa_folder(no_lift_dir, filenames)
        
        print(f"is_valid: {is_valid}")
        print(f"error_msg: {error_msg}")
        assert is_valid == False, "Test 4 failed: should be invalid"
        assert "No lift_force" in error_msg, "Test 4 failed: error message should mention missing lift file"
        print("✓ Test 4 PASSED")
        
        # Test 5: Multiple drag files
        print("\n[Test 5] Multiple drag files (should fail)")
        print("-" * 80)
        dup_drag_dir = os.path.join(tmpdir, "test_dup_drag")
        os.makedirs(dup_drag_dir, exist_ok=True)
        
        Path(os.path.join(dup_drag_dir, "lift_force_1.txt")).touch()
        Path(os.path.join(dup_drag_dir, "drag_force_1.txt")).touch()
        Path(os.path.join(dup_drag_dir, "drag_force_2.txt")).touch()
        Path(os.path.join(dup_drag_dir, "case.cas.h5")).touch()
        
        filenames = os.listdir(dup_drag_dir)
        is_valid, lift_file, drag_file, case_file, error_msg = validate_aoa_folder(dup_drag_dir, filenames)
        
        print(f"is_valid: {is_valid}")
        print(f"error_msg: {error_msg}")
        assert is_valid == False, "Test 5 failed: should be invalid"
        assert "Multiple drag files" in error_msg, "Test 5 failed: error message should mention duplicates"
        print("✓ Test 5 PASSED")
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED ✓")
    print("="*80)
    print("\nValidation system is working correctly!")
    print("The validation function will now:")
    print("  • Catch duplicate lift/drag files and skip those AoAs")
    print("  • Catch missing case files and skip those AoAs")
    print("  • Catch missing lift/drag files and skip those AoAs")
    print("  • Report all issues in the console output")
    print("  • Save validation report in processed_data.pkl for reproducibility")

if __name__ == "__main__":
    try:
        test_validation_system()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
