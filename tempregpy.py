"""The Stigler diet problem.

A description of the problem can be found here:
https://en.wikipedia.org/wiki/Stigler_diet.
"""
from tempregpy import *
import pandas as pd

# Load the Excel file
file_path = './TempRegPy.xlsx'
config = load_config(file_path)
inputs, results = build_and_run(config)
