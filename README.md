# TempRegPy
TempRegPy is a Python-based tool for optimizing hydropower dispatch. It maximizes dam profits while maintaining downstream water temperatures within ecological limits. Using real-time data, weather forecasts, and advanced algorithms, TempRegPy dynamically adjusts release, bypass, and spillage schedules to balance economic and environmental goals.

# Installation Instructions
1. Install Miniconda: Download and install [Miniconda](https://docs.anaconda.com/miniconda/) for your operating system.
2. Download the Repository: Unzip the project repository downloaded from TempRegPy [GitHub](https://github.com/energy-modelling-hub/TempRegPy) page.
3. Navigate to the Project Directory: Open a terminal and navigate to the directory where the repository was unzipped.
```python:
cd your_path
```
4. Create the Environment:
```python:
conda env create -f environment.yml
```
5. Install the Package:
```python:
pip install -e .
```

# Running the Code from CLI
To run the code from the command line interface (CLI), use the following command:

```python:
python -m tempregpy run -c path_to\TempRegPy.xlsm
```

# Running the Code from Excel
1. Enable Macros: Open the Excel file and enable macros.
2. Run Simulation: Navigate to the "Inputs" sheet and click the "Run Simulation" button at the top.

# Importing Results into Excel
1. Select Simulation Name: Choose the simulation name from the dropdown menu.
2. Read Results: Click the "Read Results" button at the top of the Excel sheet to import the results.
