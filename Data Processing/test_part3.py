
import numpy as np
import pandas as pd
from openpyxl import Workbook
from cfd_functions import create_data_summary_sheet, create_turbulence_comparison_sheet, create_coefficients_sheet

def test_excel_generation():
    print("Testing Excel Generation...")
    wb = Workbook()
    
    # Mock data
    all_data = {
        ('Config1', 'AoA_0'): {
            'lift': [1, 2, 3],
            'drag': [0.1, 0.2, 0.3],
            'turbulence_model': 'SST',
            'geometry': 'Geo1',
            'mesh': 'Mesh1',
            'version': 'V1',
            'grid': 'G1'
        }
    }
    convergence_results = {}
    num_iterations = 3
    
    print("Creating Data Summary...")
    create_data_summary_sheet(wb, all_data, num_iterations, convergence_results)
    
    print("Creating Turbulence Comparison...")
    try:
        create_turbulence_comparison_sheet(wb, all_data, num_iterations, convergence_results)
    except Exception as e:
        print(f"Error in Turbulence Comparison: {e}")

    print("Creating Coefficients...")
    create_coefficients_sheet(wb, all_data, num_iterations, convergence_results, 100)
    
    wb.save('test_output.xlsx')
    print("Success!")

if __name__ == "__main__":
    test_excel_generation()
