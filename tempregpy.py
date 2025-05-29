"""
The TempRegPy module
"""
import pandas as pd
from absl.testing.parameterized import parameters

import tempregpy as trp

# Load the Excel file
file_path = 'C:\\Projects\\GitHub\\TempRegPy\\TempRegPy_v2.xlsm'
config = trp.load_config(file_path)
config['plt_show'] =  True
inputs, results, duals = trp.build_and_run(config)

#%%
import dataretrieval.nwis as nwis

# listSiteCode = ['09261000','09234500','09260050']
listSiteCode = ['09379900','09380000','09383100'] #GCD, LF, LCR
df = nwis.get_record(sites=listSiteCode, service='iv', start='2001-01-01', end='2001-12-31')['00060'].unstack('site_no').resample('h').mean()

#%%
from ortools.math_opt.python import mathopt
import pandas as pd
import matplotlib.pyplot as plt

# Initialize LP model
model = mathopt.Model(name="Travel Time")

# Problem setup
start_time = pd.Timestamp('2001-01-04', tz='UTC')
time_travel = 24  # 24-hour TTD window
total_horizon = 168 * 4 * 1  # 4 weeks of hourly data

# Full data range, padded to allow for convolution lag
full_range = pd.date_range(
    start=start_time - pd.Timedelta(hours=time_travel),
    periods=total_horizon + time_travel,
    freq='h'
)

# Subset data from DataFrame (ensure df has UTC datetime index)
df_subset = df.loc[full_range]
df_subset = df_subset.ffill().bfill()

# Index sets
H = list(range(time_travel, total_horizon))  # Observation hours (24 .. 672)
W = list(range(time_travel))                 # TTD window (0 .. 23)

# Parameters
parameters = {
    'Q': {h: df_subset.iloc[h, 0] for h in range(-time_travel, total_horizon)},
    'Qdown': {h: df_subset.iloc[h, 1] for h in H},
    'Idown': 0,
    'wC': 100000         # Curvature weight (try 10, 100, 1000 for tuning)
}

# Variables
variables = {
    'e': [model.add_variable(lb=0, name=f'Estimation error {h}') for h in H],
    'TTD': [model.add_variable(lb=0, name=f'TTD {h}') for h in W],
    'Cmax': model.add_variable(lb=0, name='Cmax'),
    'bQdown': [model.add_variable(lb=0, name=f'bQdown {h}') for h in H]
}

# Objective: minimize total error + curvature penalty
model.minimize(
    sum(variables['e'][i] for i in range(len(H))) + parameters['wC'] * variables['Cmax']
)

# Constraints: estimation error bounds
for i, h in enumerate(H):
    model.add_linear_constraint(
        variables['bQdown'][i] - parameters['Qdown'][h] >= -variables['e'][i],
        name=f'Error lower bound {h}'
    )
    model.add_linear_constraint(
        variables['bQdown'][i] - parameters['Qdown'][h] <= variables['e'][i],
        name=f'Error upper bound {h}'
    )

# Constraints: convolution expression
for i, h in enumerate(H):
    conv_expr = sum(variables['TTD'][h_prime] * parameters['Q'].get(h - h_prime, 0.0) for h_prime in W)
    model.add_linear_constraint(variables['bQdown'][i] == conv_expr + parameters['Idown'], name=f'Flow match {h}')

# Constraints: curvature regularization
for h in W[1:-1]:
    curvature_expr = (variables['TTD'][h + 1] - 2 * variables['TTD'][h] + variables['TTD'][h - 1])
    model.add_linear_constraint(curvature_expr >= -variables['Cmax'], name=f'Curvature lower {h}')
    model.add_linear_constraint(curvature_expr <= variables['Cmax'], name=f'Curvature upper {h}')

# Constraints: TTD must integrate to 1
model.add_linear_constraint(sum(variables['TTD'][h] for h in W) == 1, name='TTD_mass')

# Solve
results = mathopt.solve(model, mathopt.SolverType.HIGHS)


import pandas as pd

result = {}
for var in ['e', 'TTD', 'bQdown']:
    # Get the variable values from the results
    values = results.variable_values(variables[var])

    # Convert the values to a DataFrame
    if isinstance(values, dict):
        # If values are a dictionary, convert it to a DataFrame
        result[var] = pd.DataFrame.from_dict(values, orient='index', columns=[var])
    else:
        # If values are a list, convert it to a DataFrame
        result[var] = pd.DataFrame(values, columns=[var])

# Handle Cmax separately since it's a single float value
cmax_value = results.variable_values(variables['Cmax'])
result['Cmax'] = pd.DataFrame([cmax_value], columns=['Cmax'])

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 5))

# Plot TTD
result['TTD'].plot(ax=ax, color='steelblue', linewidth=2, marker='o', markersize=4)

# Titles and labels
ax.set_title('Estimated Travel Time Distribution (TTD) - GCD -> RM61', fontsize=16)
ax.set_xlabel('Lag (hours)', fontsize=12)
ax.set_ylabel('Fraction of Release', fontsize=12)

# Grid, limits, and style
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xlim(left=0)  # optional: set left bound to 0
ax.set_ylim(bottom=0)  # optional: keep y positive

# Tick customization
ax.tick_params(axis='both', labelsize=10)

# Tight layout for better spacing
plt.tight_layout()

# Show plot
plt.show()

print(result['TTD'].sum())