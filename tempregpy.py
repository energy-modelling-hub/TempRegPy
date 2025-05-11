"""
The TempRegPy module
"""
import tempregpy as trp

# Load the Excel file
config = trp.load_config_from_excel("./TempRegPy_GCD_LoadDriven.xlsm")
inputs, results, duals = trp.build_and_run(config)

print('A')