"""
The TempRegPy module
"""
import tempregpy as trp
import pandas as pd

# Load the Excel file
file_path = 'C:\\Users\\mpavicevic\\Desktop\\test\\TempRegPy.xlsx'
config = trp.load_config(file_path)
inputs, results = trp.build_and_run(config)
