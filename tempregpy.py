"""
The TempRegPy module
"""
import tempregpy as trp

# Load the Excel file
file_path = 'C:\\Projects\\GitHub\\TempRegPy\\TempRegPy_test.xlsm'
config = trp.load_config(file_path)
inputs, results, duals = trp.build_and_run(config)

print('A')