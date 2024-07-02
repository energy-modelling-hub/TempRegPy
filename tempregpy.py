"""
The TempRegPy module
"""
import tempregpy as trp

# Load the Excel file
file_path = 'C:\\Projects\\GitHub\\TempRegPy\\TempRegPy.xlsm'
config = trp.load_config(file_path)
inputs, results = trp.build_and_run(config)
