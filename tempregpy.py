"""The Stigler diet problem.

A description of the problem can be found here:
https://en.wikipedia.org/wiki/Stigler_diet.
"""
from ortools.linear_solver import pywraplp
import pandas as pd
from tempregpy import *
import random


import pandas as pd

# Load the Excel file
file_path = './TempRegPy.xlsx'
excel_data = pd.ExcelFile(file_path)

# Parse the relevant sheet
df = excel_data.parse('Inputs')

# Initialize the input_data dictionary
input_data = {}

# Populate the input_data dictionary
input_data['Q_tot_daily'] = df.loc[df['Python Variable Names'] == 'Q_tot_daily', 'Single input'].values[0]
input_data['Q_max_daily_change'] = df.loc[df['Python Variable Names'] == 'Q_max_daily_change', 'Single input'].values[0]
input_data['Q_bp_ramp_down_max'] = df.loc[df['Python Variable Names'] == 'Q_bp_ramp_down_max', 'Single input'].values[0]
input_data['Q_bp_ramp_up_max'] = df.loc[df['Python Variable Names'] == 'Q_bp_ramp_up_max', 'Single input'].values[0]
input_data['Q_tur_ramp_down_max'] = df.loc[df['Python Variable Names'] == 'Q_tur_ramp_down_max', 'Single input'].values[0]
input_data['Q_tur_ramp_up_max'] = df.loc[df['Python Variable Names'] == 'Q_tur_ramp_up_max', 'Single input'].values[0]
input_data['Q_tot_ramp_up_max'] = df.loc[df['Python Variable Names'] == 'Q_tot_ramp_up_max', 'Single input'].values[0]
input_data['Q_tot_ramp_down_max'] = df.loc[df['Python Variable Names'] == 'Q_tot_ramp_down_max', 'Single input'].values[0]
input_data['T_ramp_up_delta'] = df.loc[df['Python Variable Names'] == 'T_ramp_up_delta', 'Single input'].values[0]
input_data['T_ramp_down_delta'] = df.loc[df['Python Variable Names'] == 'T_ramp_down_delta', 'Single input'].values[0]
input_data['T_RM61_daily'] = df.loc[df['Python Variable Names'] == 'T_RM61_daily', 'Single input'].values[0]
input_data['dT_daily'] = df.loc[df['Python Variable Names'] == 'dT_daily', 'Single input'].values[0]
input_data['WaterToPowerConversion'] = df.loc[df['Python Variable Names'] == 'WaterToPowerConversion', 'Single input'].values[0]
# input_data['P_tur_min_values'] = df.loc[df['Python Variable Names'] == 'P_tur_min_values', 'Single input'].values[0]
# input_data['P_tur_max_values'] = df.loc[df['Python Variable Names'] == 'P_tur_max_values', 'Single input'].values[0]


# Hourly values
hours = [f'H{i:02}' for i in range(1, 25)]

for var in ['Q_bp_min_values', 'Q_bp_max_values', 'Q_tur_min_values', 'Q_tur_max_values', 'Q_tot_min_values', 'Q_tot_max_values',
            'T_bp_values', 'T_tur_values', 'T_RM61_hourly_max_values', 'T_RM61_hourly_min_values', 'dT_hourly_values',
            'LMP_values', 'Demand_values', 'P_tur_min_values', 'P_tur_max_values']:
    input_data[var] = df.loc[df['Python Variable Names'] == var, hours].values.flatten().tolist()

# Penalty costs
for var in ['C_bp_ramp_up', 'C_bp_ramp_down', 'C_tur_ramp_up', 'C_tur_ramp_down', 'C_tot_ramp_up', 'C_tot_ramp_down']:
    input_data[var] = df.loc[df['Python Variable Names'] == var, 'Single input'].values[0]


# Sets
time = ["t{:02}".format(i) for i in range(1, 25)]
units = ["UnitA"]
plants = ["PlantA"]

# input_data = {}
# # Parameters
# input_data['LMP_values'] = [46.85, 45.06, 43.83, 42.55, 42.62, 46.61, 76.48, 77.49, 73.64, 68.51, 67.62, 69.34, 69.23, 74.68, 86.84, 97.79, 91.29, 99.07, 103.56, 108.67, 98.73, 91.91, 53.34, 48.72]
# input_data['T_RM61_hourly_max_values'] = [15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 18, 18, 18, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5]
# input_data['T_RM61_hourly_min_values'] = [14 for i in range (1, 25)] # °C
# input_data['dT_hourly_values'] = [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]
# input_data['T_ramp_up_delta'] = 0 # °C
# input_data['T_ramp_down_delta'] = 0 # °C
# input_data['T_RM61_daily'] = 15.5 # °C
# input_data['dT_daily'] = 1.5 # °C
# input_data['T_bp_values'] = [7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5] # °C
# input_data['T_tur_values'] = [15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5] # °C
# input_data['Demand_values'] = [1000 for i in range (1, 25)] # MW
# input_data['Q_tot_daily'] = 235003 # CFS
# input_data['Q_max_daily_change'] = 8000 # CFS
# input_data['WaterToPowerConversion'] = 0.0354538 # MW/CFS
# input_data['Q_bp_min_values'] = [0 for i in range (1, 25)] # CFS
# input_data['Q_bp_max_values'] = [15000 for i in range (1, 25)] # CFS
# input_data['Q_tur_min_values'] = [2400 for i in range (1, 25)] # CFS
# input_data['Q_tur_max_values'] = [25000 for i in range (1, 25)] # CFS
# input_data['Q_tot_min_values'] = [7000 for i in range (1, 25)] # CFS
# input_data['Q_tot_max_values'] = [12100 for i in range (1, 25)] # CFS
# input_data['Q_bp_ramp_down_max'] = 15000
# input_data['Q_bp_ramp_up_max'] = 15000
# input_data['Q_tur_ramp_down_max'] = 4000
# input_data['Q_tur_ramp_up_max'] = 25000
# input_data['Q_tot_ramp_up_max'] = 4000 # CFS/h
# input_data['Q_tot_ramp_down_max'] = 2500 # CFS/h
# input_data['C_bp_ramp_up'] = 1
# input_data['C_bp_ramp_down'] = 1
# input_data['C_tur_ramp_up'] = 1
# input_data['C_tur_ramp_down'] = 1
# input_data['C_tot_ramp_up'] = 1
# input_data['C_tot_ramp_down'] = 1
# input_data['P_tur_max_values'] = [1000 for i in range (1, 25)] # CFS
# input_data['P_tur_min_values'] = [0 for i in range (1, 25)] # CFS

# maximum release within 24h cant be more than X
# daily total change 8000 CFS 8000 <= qtot_t - qtot_t+dt <=8000 (for all hours)
# q_tot_t > qmin q_tot_t <= 8000

hulls = {}
### Compute hull coefficients
data_gen = DataGenerator(input_data['Q_tur_min_values'], input_data['Q_tur_max_values'], input_data['Q_bp_min_values'], input_data['Q_bp_max_values'], input_data['Q_tot_min_values'], input_data['Q_tot_max_values'])
hulls['hull_X'] = HullComputation(data_gen.points_X, "X = Q_bp * Q_tur1")
hulls['hull_Y'] = HullComputation(data_gen.points_Y, "Y = Q_tur * Q_bp1")
hulls['hull_Z'] = HullComputation(data_gen.points_Z, "Z = Q_tot * Q_tot1")

hulls['hull_X'].print_plane_equations()
hulls['hull_Y'].print_plane_equations()
hulls['hull_Z'].print_plane_equations()

Plotter(data_gen, hulls['hull_X'], hulls['hull_Y'], hulls['hull_Z'])

### Assign parameters
parameters = {}
parameters['LMP'] = {(t): input_data['LMP_values'][i] for i, t in enumerate(time)}
parameters['T_RM61_hourly_max'] = {(t): input_data['T_RM61_hourly_max_values'][i] for i, t in enumerate(time)}
parameters['T_RM61_hourly_min'] = {(t): input_data['T_RM61_hourly_min_values'][i] for i, t in enumerate(time)}
parameters['dT_hourly'] = {(t): input_data['dT_hourly_values'][i] for i, t in enumerate(time)}
parameters['T_bp'] = {(t, u): input_data['T_bp_values'][i] for i, t in enumerate(time) for u in units}
parameters['T_tur'] = {(t, u): input_data['T_tur_values'][i] for i, t in enumerate(time) for u in units}
parameters['Q_bp_min'] = {(t, u): input_data['Q_bp_min_values'][i] for i, t in enumerate(time) for u in units}
parameters['Q_bp_max'] = {(t, u): input_data['Q_bp_max_values'][i] for i, t in enumerate(time) for u in units}
parameters['Q_tur_min'] = {(t, u): input_data['Q_tur_min_values'][i] for i, t in enumerate(time) for u in units}
parameters['Q_tur_max'] = {(t, u): input_data['Q_tur_max_values'][i] for i, t in enumerate(time) for u in units}
parameters['P_tur_min'] = {(t, u): input_data['P_tur_min_values'][i] for i, t in enumerate(time) for u in units}
parameters['P_tur_max'] = {(t, u): input_data['P_tur_max_values'][i] for i, t in enumerate(time) for u in units}
parameters['Q_tot_min'] = {t: input_data['Q_tot_min_values'][i] for i, t in enumerate(time)}
parameters['Q_tot_max'] = {t: input_data['Q_tot_max_values'][i] for i, t in enumerate(time)}
parameters['Demand'] = {(t): input_data['Demand_values'][i] for i, t in enumerate(time)}

# Create solver
solver = pywraplp.Solver.CreateSolver('GLOP')

variables = {}
# Variables
variables['q_bp'] = {(t, u): solver.NumVar(parameters['Q_bp_min'][t, u], parameters['Q_bp_max'][t, u], 'q_bp[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tur'] = {(t, u): solver.NumVar(parameters['Q_tur_min'][t, u], parameters['Q_tur_max'][t, u], 'q_tur[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tot'] = {(t, u): solver.NumVar(parameters['Q_tot_min'][t], parameters['Q_tot_max'][t], 'q_tot[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_bp_t_tur_t1'] = {(t, u): solver.NumVar(parameters['Q_bp_min'][t, u]*parameters['Q_tur_min'][t,u], parameters['Q_bp_max'][t,u]*parameters['Q_tur_max'][t,u], 'q_bp_t_tur_t1[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tur_t_bp_t1'] = {(t, u): solver.NumVar(parameters['Q_bp_min'][t,u]*parameters['Q_tur_min'][t,u], parameters['Q_bp_max'][t,u]*parameters['Q_tur_max'][t,u], 'q_tur_t_bp_t1[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tot_t_tot_t1'] = {(t, u): solver.NumVar(parameters['Q_tot_min'][t]*parameters['Q_tot_min'][t], parameters['Q_tot_max'][t]*parameters['Q_tot_max'][t], 'q_tot_t_tot_t1[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_bp_ramp_up'] = {(t, u): solver.NumVar(0, input_data['Q_bp_ramp_up_max'], 'q_bp_ramp_up[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_bp_ramp_down'] = {(t, u): solver.NumVar(0, input_data['Q_bp_ramp_down_max'], 'q_bp_ramp_down[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tur_ramp_up'] = {(t, u): solver.NumVar(0, input_data['Q_tur_ramp_up_max'], 'q_tur_ramp_up[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tur_ramp_down'] = {(t, u): solver.NumVar(0, input_data['Q_tur_ramp_down_max'], 'q_tur_ramp_down[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tot_ramp_up'] = {(t, u): solver.NumVar(0, input_data['Q_tot_ramp_up_max'], 'q_tot_ramp_up[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tot_ramp_down'] = {(t, u): solver.NumVar(0, input_data['Q_tot_ramp_down_max'], 'q_tot_ramp_down[%s,%s]' % (t, u)) for t in time for u in units}
variables['q_tot_min'] = {(u): solver.NumVar(min(parameters['Q_tot_min'].values()), max(parameters['Q_tot_max'].values()), 'q_tot_min[%s]' % (u)) for u in units}
variables['p_tur'] = {(t, u): solver.NumVar(parameters['P_tur_min'][t, u], parameters['P_tur_max'][t, u], 'p_tur[%s,%s]' % (t, u)) for t in time for u in units}

# Constraints
constraints = []
constraint_id_main = []
constraint_id_unit = []
constraint_id_time = []

# Add constraints for total hourly release
for u in units:
    for t in time:
        constraint_id_main.append(f'Total hourly release')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        constraints.append(solver.Add(variables['q_bp'][t, u] + variables['q_tur'][t, u] == variables['q_tot'][t, u]))

# Add constraint for total daily release
constraint_id_main.append('Total daily release')
constraint_id_unit.append(f'')
constraint_id_time.append(f'')
constraints.append(solver.Add(sum(variables['q_tot'][t, u] for u in units for t in time) == input_data['Q_tot_daily']))

# Add constraints for maximum average daily temperature
constraint_id_main.append(f'Maximum average daily temperature')
constraint_id_unit.append(f'')
constraint_id_time.append(f'')
constraints.append(
    solver.Add(sum(variables['q_bp'][t, u] * parameters['T_bp'][t, u] + variables['q_tur'][t, u] * parameters['T_tur'][t, u] for u in units for t in time) <=
               (input_data['T_RM61_daily'] - input_data['dT_daily']) * sum(variables['q_tot'][t, u] for u in units for t in time)))
    # solver.Add(sum(variables['q_bp'][t, u] * parameters['T_bp'][t, u] + variables['q_tur'][t, u] * parameters['T_tur'][t, u] for u in units for t in time) <=
    #            sum((input_data['T_RM61_daily'] - parameters['dT_hourly'][t]) * variables['q_tot'][t, u] for u in units for t in time)))


constraint_id_main.append(f'Temperature t01 = t24')
constraint_id_unit.append(f'')
constraint_id_time.append(f'')
constraints.append(solver.Add(sum(variables['q_bp'][time[0], u] * parameters['T_bp'][time[0], u] + variables['q_tur'][time[0], u] * parameters['T_tur'][time[0], u] for u in units) ==
                              sum(variables['q_bp'][time[-1], u] * parameters['T_bp'][time[-1], u] + variables['q_tur'][time[-1], u] * parameters['T_tur'][time[-1], u] for u in units)))

for t in time:
    # Add constraints for maximum total daily ramping rate 8000CFS
    constraint_id_main.append(f'Maximum daily operating range - min')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(
        solver.Add(sum(variables['q_tot_min'][u] for u in units) <= sum(variables['q_tot'][t, u] for u in units)))

for t in time:
    # Add constraints for maximum total daily ramping rate 8000CFS
    constraint_id_main.append(f'Maximum daily operating range - max')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(
        solver.Add(sum(variables['q_tot_min'][u] for u in units) + 8000 >= sum(variables['q_tot'][t, u] for u in units)))

# Add constraints for maximum hourly temperature
for t in time:
    constraint_id_main.append(f'Maximum hourly temperature')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(solver.Add(sum(variables['q_bp'][t, u] * parameters['T_bp'][t, u] + variables['q_tur'][t, u] * parameters['T_tur'][t, u] for u in units) <=
                                  (parameters['T_RM61_hourly_max'][t] - parameters['dT_hourly'][t]) * sum(variables['q_tot'][t, u] for u in units)))

# Add constraints for minimum hourly temperature
for t in time:
    constraint_id_main.append(f'Minimum hourly temperature')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(solver.Add(sum(variables['q_bp'][t, u] * parameters['T_bp'][t, u] + variables['q_tur'][t, u] * parameters['T_tur'][t, u] for u in units) >=
                                  (parameters['T_RM61_hourly_min'][t] - parameters['dT_hourly'][t]) * sum(variables['q_tot'][t, u] for u in units)))

# Add constraints for power balance

for u in units:
    for t in time:
        constraint_id_main.append(f'Power Output')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        constraints.append(solver.Add(variables['p_tur'][t, u] == variables['q_tur'][t, u] * input_data['WaterToPowerConversion']))

# Add constraints for power balance
for t in time:
    constraint_id_main.append(f'Power Demand Balance')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(solver.Add(parameters['Demand'][t] - sum(variables['p_tur'][t, u] for u in units) >= 0))

# Add constraint for bypass ramping up rate
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        # Add ramp up constraints
        # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
        constraint_id_main.append(f'Bypass ramping')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add(variables['q_bp'][time[0], u] - variables['q_bp'][time[-1], u] <= variables['q_bp_ramp_up'][t, u]))
        else:
            constraints.append(solver.Add(variables['q_bp'][t, u] - variables['q_bp'][prev_t, u] <= variables['q_bp_ramp_up'][t, u]))

# Add constraint for bypass ramping down rate
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        # Add ramp up constraints
        # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
        constraint_id_main.append(f'Bypass ramping')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add(variables['q_bp'][time[-1], u] - variables['q_bp'][time[0], u] <= variables['q_bp_ramp_down'][t, u]))
        else:
            constraints.append(solver.Add(variables['q_bp'][prev_t, u] - variables['q_bp'][t, u] <= variables['q_bp_ramp_down'][t, u]))

# Add constraint for turbine ramping up rate
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        # Add ramp up constraints
        # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
        constraint_id_main.append(f'Turbine ramping')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add(variables['q_tur'][time[0], u] - variables['q_tur'][time[-1], u] <= variables['q_tur_ramp_up'][t, u]))
        else:
            constraints.append(solver.Add(variables['q_tur'][t, u] - variables['q_tur'][prev_t, u] <= variables['q_tur_ramp_up'][t, u]))

# Add constraint for turbine ramping down rate
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        # Add ramp up constraints
        # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
        constraint_id_main.append(f'Turbine ramping')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add(variables['q_tur'][time[-1], u] - variables['q_tur'][time[0], u] <= variables['q_tur_ramp_down'][t, u]))
        else:
            constraints.append(solver.Add(variables['q_tur'][prev_t, u] - variables['q_tur'][t, u] <= variables['q_tur_ramp_down'][t, u]))


# Add constraint for total ramping up constraint
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        # Add ramp up constraints
        # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
        constraint_id_main.append(f'Ramp up constraint')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add(variables['q_tot'][time[0], u] - variables['q_tot'][time[-1], u] <= variables['q_tot_ramp_up'][t, u]))
        else:
            constraints.append(solver.Add(variables['q_tot'][t, u] - variables['q_tot'][prev_t, u] <= variables['q_tot_ramp_up'][t, u]))

# Add constraint for total ramping down constraint
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        constraint_id_main.append(f'Ramp down constraint')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add(variables['q_tot'][time[-1], u] - variables['q_tot'][time[0], u] <= variables['q_tot_ramp_down'][t, u]))
        else:
            constraints.append(solver.Add(variables['q_tot'][prev_t, u] - variables['q_tot'][t, u] <= variables['q_tot_ramp_down'][t, u]))

#####################################################################
##### Hull surface area constraints
for u in units:
    for t in time:
        constraint_id_main.append(f'Initial Temperature ramp up constraint')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        constraints.append(solver.Add((variables['q_bp_t_tur_t1'][t, u] - variables['q_tur_t_bp_t1'][t, u])*(parameters['T_bp'][t, u] - parameters['T_tur'][t, u]) <=
                                      input_data['T_ramp_up_delta'] * variables['q_tot_t_tot_t1'][t, u]))

for u in units:
    for t in time:
        constraint_id_main.append(f'Initial Temperature ramp down constraint')
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        constraints.append(solver.Add((variables['q_bp_t_tur_t1'][t, u] - variables['q_tur_t_bp_t1'][t, u])*(parameters['T_bp'][t, u] - parameters['T_tur'][t, u]) >=
                                      -input_data['T_ramp_down_delta'] * variables['q_tot_t_tot_t1'][t, u]))

for j in range(0,4):
    for u in units:
        for i in range(len(time)):
            t = time[i]
            prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
            constraint_id_main.append(f'Hull constraint: Surface' + str(j) + ' for ' + hulls['hull_X'].label)
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            if i == 0:
                if hulls['hull_X'].inequality_signs[j] == '<=':
                    constraints.append(solver.Add(hulls['hull_X'].plane_equations[j][0]*variables['q_bp'][time[0], u] +
                                                  hulls['hull_X'].plane_equations[j][1]*variables['q_tur'][time[-1], u] +
                                                  hulls['hull_X'].plane_equations[j][2]*variables['q_bp_t_tur_t1'][time[0], u] <=
                                                  hulls['hull_X'].plane_equations[j][3]))
                if hulls['hull_X'].inequality_signs[j] == '>=':
                    constraints.append(solver.Add(hulls['hull_X'].plane_equations[j][0]*variables['q_bp'][time[0], u] +
                                                  hulls['hull_X'].plane_equations[j][1]*variables['q_tur'][time[-1], u] +
                                                  hulls['hull_X'].plane_equations[j][2]*variables['q_bp_t_tur_t1'][time[0], u] >=
                                                  hulls['hull_X'].plane_equations[j][3]))
            else:
                if hulls['hull_X'].inequality_signs[j] == '<=':
                    constraints.append(solver.Add(hulls['hull_X'].plane_equations[j][0] * variables['q_bp'][t, u] +
                                                  hulls['hull_X'].plane_equations[j][1] * variables['q_tur'][prev_t, u] +
                                                  hulls['hull_X'].plane_equations[j][2] * variables['q_bp_t_tur_t1'][t, u] <=
                                                  hulls['hull_X'].plane_equations[j][3]))
                if hulls['hull_X'].inequality_signs[j] == '>=':
                    constraints.append(solver.Add(hulls['hull_X'].plane_equations[j][0] * variables['q_bp'][t, u] +
                                                  hulls['hull_X'].plane_equations[j][1] * variables['q_tur'][prev_t, u] +
                                                  hulls['hull_X'].plane_equations[j][2] * variables['q_bp_t_tur_t1'][t, u] >=
                                                  hulls['hull_X'].plane_equations[j][3]))

for j in range(0,4):
    for u in units:
        for i in range(len(time)):
            t = time[i]
            prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
            constraint_id_main.append(f'Hull constraint: Surface' + str(j) + ' for ' + hulls['hull_Y'].label)
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            if i == 0:
                if hulls['hull_Y'].inequality_signs[j] == '<=':
                    constraints.append(solver.Add(hulls['hull_Y'].plane_equations[j][0]*variables['q_tur'][time[0], u] +
                                                  hulls['hull_Y'].plane_equations[j][1]*variables['q_bp'][time[-1], u] +
                                                  hulls['hull_Y'].plane_equations[j][2]*variables['q_tur_t_bp_t1'][time[0], u] <=
                                                  hulls['hull_Y'].plane_equations[j][3]))
                if hulls['hull_Y'].inequality_signs[j] == '>=':
                    constraints.append(solver.Add(hulls['hull_Y'].plane_equations[j][0]*variables['q_tur'][time[0], u] +
                                                  hulls['hull_Y'].plane_equations[j][1]*variables['q_bp'][time[-1], u] +
                                                  hulls['hull_Y'].plane_equations[j][2]*variables['q_tur_t_bp_t1'][time[0], u] >=
                                                  hulls['hull_Y'].plane_equations[j][3]))
            else:
                if hulls['hull_Y'].inequality_signs[j] == '<=':
                    constraints.append(solver.Add(hulls['hull_Y'].plane_equations[j][0] * variables['q_tur'][t, u] +
                                                  hulls['hull_Y'].plane_equations[j][1] * variables['q_bp'][prev_t, u] +
                                                  hulls['hull_Y'].plane_equations[j][2] * variables['q_tur_t_bp_t1'][t, u] <=
                                                  hulls['hull_Y'].plane_equations[j][3]))
                if hulls['hull_Y'].inequality_signs[j] == '>=':
                    constraints.append(solver.Add(hulls['hull_Y'].plane_equations[j][0] * variables['q_tur'][t, u] +
                                                  hulls['hull_Y'].plane_equations[j][1] * variables['q_bp'][prev_t, u] +
                                                  hulls['hull_Y'].plane_equations[j][2] * variables['q_tur_t_bp_t1'][t, u] >=
                                                  hulls['hull_Y'].plane_equations[j][3]))

for j in range(0,4):
    for u in units:
        for i in range(len(time)):
            t = time[i]
            prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
            constraint_id_main.append(f'Hull constraint: Surface' + str(j) + ' for ' + hulls['hull_Z'].label)
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            if i == 0:
                if hulls['hull_Z'].inequality_signs[j] == '<=':
                    constraints.append(solver.Add(hulls['hull_Z'].plane_equations[j][0]*variables['q_tot'][time[0], u] +
                                                  hulls['hull_Z'].plane_equations[j][1]*variables['q_tot'][time[-1], u] +
                                                  hulls['hull_Z'].plane_equations[j][2]*variables['q_tot_t_tot_t1'][time[0], u] <=
                                                  hulls['hull_Z'].plane_equations[j][3]))
                if hulls['hull_Z'].inequality_signs[j] == '>=':
                    constraints.append(solver.Add(hulls['hull_Z'].plane_equations[j][0]*variables['q_tot'][time[0], u] +
                                                  hulls['hull_Z'].plane_equations[j][1]*variables['q_tot'][time[-1], u] +
                                                  hulls['hull_Z'].plane_equations[j][2]*variables['q_tot_t_tot_t1'][time[0], u] >=
                                                  hulls['hull_Z'].plane_equations[j][3]))
            else:
                if hulls['hull_Z'].inequality_signs[j] == '<=':
                    constraints.append(solver.Add(hulls['hull_Z'].plane_equations[j][0] * variables['q_tot'][t, u] +
                                                  hulls['hull_Z'].plane_equations[j][1] * variables['q_tot'][prev_t, u] +
                                                  hulls['hull_Z'].plane_equations[j][2] * variables['q_tot_t_tot_t1'][t, u] <=
                                                  hulls['hull_Z'].plane_equations[j][3]))
                if hulls['hull_Z'].inequality_signs[j] == '>=':
                    constraints.append(solver.Add(hulls['hull_Z'].plane_equations[j][0] * variables['q_tot'][t, u] +
                                                  hulls['hull_Z'].plane_equations[j][1] * variables['q_tot'][prev_t, u] +
                                                  hulls['hull_Z'].plane_equations[j][2] * variables['q_tot_t_tot_t1'][t, u] >=
                                                  hulls['hull_Z'].plane_equations[j][3]))

# Additional hull constraints
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        constraint_id_main.append(f'Hull constraint: Ramping down for ' + hulls['hull_X'].label)
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add((parameters['Q_bp_min'][time[0], u] - input_data['Q_bp_ramp_down_max']) * variables['q_tur'][time[-1], u] <= variables['q_bp_t_tur_t1'][time[0], u]))
        else:
            constraints.append(solver.Add((parameters['Q_bp_min'][t, u]-input_data['Q_bp_ramp_down_max'])*variables['q_tur'][prev_t, u] <= variables['q_bp_t_tur_t1'][t, u]))

# Additional hull constraints
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        constraint_id_main.append(f'Hull constraint: Ramping up for ' + hulls['hull_X'].label)
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add((parameters['Q_bp_max'][time[0], u] + input_data['Q_bp_ramp_up_max']) * variables['q_tur'][time[-1], u] >= variables['q_bp_t_tur_t1'][time[0], u]))
        else:
            constraints.append(solver.Add((parameters['Q_bp_max'][t, u] + input_data['Q_bp_ramp_up_max'])*variables['q_tur'][prev_t, u] >= variables['q_bp_t_tur_t1'][t, u]))

# Additional hull constraints
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        constraint_id_main.append(f'Hull constraint: Ramping down for ' + hulls['hull_Y'].label)
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add((parameters['Q_tur_min'][time[0], u] - input_data['Q_tur_ramp_down_max']) * variables['q_bp'][time[-1], u] <= variables['q_tur_t_bp_t1'][time[0], u]))
        else:
            constraints.append(solver.Add((parameters['Q_tur_min'][t, u]-input_data['Q_tur_ramp_down_max'])*variables['q_bp'][prev_t, u] <= variables['q_tur_t_bp_t1'][t, u]))

# Additional hull constraints
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        constraint_id_main.append(f'Hull constraint: Ramping up for ' + hulls['hull_Y'].label)
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add((parameters['Q_tur_max'][time[0], u] + input_data['Q_tur_ramp_up_max']) * variables['q_bp'][time[-1], u] >= variables['q_tur_t_bp_t1'][time[0], u]))
        else:
            constraints.append(solver.Add((parameters['Q_tur_max'][t, u] + input_data['Q_tur_ramp_up_max'])*variables['q_bp'][prev_t, u] >= variables['q_tur_t_bp_t1'][t, u]))

# Additional hull constraints
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        constraint_id_main.append(f'Hull constraint: Ramping down for ' + hulls['hull_Z'].label)
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add((parameters['Q_tot_min'][time[0]] - input_data['Q_tot_ramp_down_max']) * variables['q_tot'][time[-1], u] <= variables['q_tot_t_tot_t1'][time[0], u]))
        else:
            constraints.append(solver.Add((parameters['Q_tot_min'][t]-input_data['Q_tot_ramp_down_max'])*variables['q_tot'][prev_t, u] <= variables['q_tot_t_tot_t1'][t, u]))

# Additional hull constraints
for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        constraint_id_main.append(f'Hull constraint: Ramping up for ' + hulls['hull_Z'].label)
        constraint_id_unit.append(f'{u}')
        constraint_id_time.append(f'{t}')
        if i == 0:
            constraints.append(solver.Add((parameters['Q_tot_max'][time[0]] + input_data['Q_tot_ramp_up_max']) * variables['q_tot'][time[-1], u] >= variables['q_tot_t_tot_t1'][time[0], u]))
        else:
            constraints.append(solver.Add((parameters['Q_tot_max'][t] + input_data['Q_tot_ramp_up_max'])*variables['q_tot'][prev_t, u] >= variables['q_tot_t_tot_t1'][t, u]))


# Objective
objective = solver.Objective()
for u in units:
    for t in time:
        objective.SetCoefficient(variables['p_tur'][t, u], parameters['LMP'][t])
        objective.SetCoefficient(variables['q_bp_ramp_down'][t, u], -input_data['C_bp_ramp_down'])
        objective.SetCoefficient(variables['q_bp_ramp_up'][t, u], -input_data['C_bp_ramp_up'])
        objective.SetCoefficient(variables['q_tur_ramp_down'][t, u], -input_data['C_tur_ramp_down'])
        objective.SetCoefficient(variables['q_tur_ramp_up'][t, u], -input_data['C_tur_ramp_up'])
        objective.SetCoefficient(variables['q_tot_ramp_down'][t, u], -input_data['C_tot_ramp_down'])
        objective.SetCoefficient(variables['q_tot_ramp_up'][t, u], -input_data['C_tot_ramp_up'])

objective.SetMaximization()

# Solve the problem
status = solver.Solve()


def process_u_t_data(variable, input=False):
    if input is False:
        data = {(t, u): variable[t, u].solution_value() for t in time for u in units}
    else:
        data = {(t, u): variable[t, u] for t in time for u in units}
    # Extract unit names and column names
    unit_names = sorted(set(unit for (_, unit) in data.keys()))
    column_names = sorted(set(column for (column, _) in data.keys()))

    # Convert dictionary to DataFrame
    df = pd.DataFrame(data.values(), index=pd.MultiIndex.from_tuples(data.keys()), columns=['Values'])

    # Reshape DataFrame to desired format
    df = df.unstack().squeeze().to_frame().T

    # Set index and columns
    df.index = unit_names
    df.columns = column_names
    return df

def process_t_data(variable, input=False, col_name=''):
    if input is False:
        data = {(t): variable[t].solution_value() for t in time}
    else:
        data = {(t): variable[t] for t in time}
    # Extract unit names and column names
    index_names = sorted(set(column for (column) in data.keys()))

    # Convert dictionary to DataFrame
    df = pd.DataFrame(data.values(), columns=[col_name])

    # Set index and columns
    df.index = index_names
    return df

def process_u_data(variable, input=False, col_name=''):
    if input is False:
        data = {(u): variable[u].solution_value() for u in units}
    else:
        data = {(t): variable[u] for u in units}
    # Extract unit names and column names
    index_names = sorted(set(column for (column) in data.keys()))

    # Convert dictionary to DataFrame
    df = pd.DataFrame(data.values(), columns=[col_name])

    # Set index and columns
    df.index = index_names
    return df

def export_dual_values(constraints, constraint_id_main, constraint_id_unit, constraint_id_time):
    dual_values = pd.DataFrame({
        'Constraint Name': constraint_id_main,
        'Constraint idx1': constraint_id_unit,
        'Constraint idx2': constraint_id_time,
        'Dual Value': [constraint.dual_value() for constraint in constraints]
    })
    return dual_values

# Check if the problem has an optimal solution
if status == pywraplp.Solver.OPTIMAL:
    print('Objective value =', objective.Value())
    results = {}
    results['Objective Value'] = objective.Value()
    results['q_tur'] = process_u_t_data(variables['q_tur'])
    results['q_bp'] = process_u_t_data(variables['q_bp'])
    results['q_tot'] = process_u_t_data(variables['q_tot'])
    results['p_tur'] = process_u_t_data(variables['p_tur'])
    results['q_bp_t_tur_t1'] = process_u_t_data(variables['q_bp_t_tur_t1'])
    results['q_tur_t_bp_t1'] = process_u_t_data(variables['q_tur_t_bp_t1'])
    results['q_tot_t_tot_t1'] = process_u_t_data(variables['q_tot_t_tot_t1'])
    results['q_bp_ramp_up'] = process_u_t_data(variables['q_bp_ramp_up'])
    results['q_bp_ramp_down'] = process_u_t_data(variables['q_bp_ramp_down'])
    results['q_tur_ramp_up'] = process_u_t_data(variables['q_tur_ramp_up'])
    results['q_tur_ramp_down'] = process_u_t_data(variables['q_tur_ramp_down'])
    results['q_tot_ramp_up'] = process_u_t_data(variables['q_tot_ramp_up'])
    results['q_tot_ramp_down'] = process_u_t_data(variables['q_tot_ramp_down'])
    results['T_dam'] = (results['q_tur'] * process_u_t_data(parameters['T_tur'], input=True) + results['q_bp'] * process_u_t_data(parameters['T_bp'], input=True)) / results['q_tot']
    results['T_RM61'] = results['T_dam'].T + process_t_data(parameters['dT_hourly'], input=True,col_name='UnitA')
    results['T_RM61'].columns = ['T_RM61']
    results['Dual Values'] = export_dual_values(constraints, constraint_id_main, constraint_id_unit, constraint_id_time)
    results['q_tot_min'] = process_u_data(variables['q_tot_min'])

    # Export results to a file
    with open('optimization_results.txt', 'w') as f:
        f.write('Results:\n')
        f.write(f'Objective Value: {objective.Value()}\n\n')

        for key, value in results.items():
            if isinstance(value, pd.DataFrame):
                f.write(f'{key}:\n{value.to_string()}\n\n')
            else:
                f.write(f'{key}: {value}\n')

else:
    print('The problem does not have an optimal solution.')


def concat_and_rename(results, q_tur_value, q_bp_value, unit_name='UnitA'):
    # Selecting desired rows from each dataframe
    q_tur_selected = results[q_tur_value].loc[unit_name, :]
    q_bp_selected = results[q_bp_value].loc[unit_name, :]

    # Concatenating them
    concatenated_df = pd.concat([q_bp_selected, q_tur_selected], axis=1)

    # Assigning index names
    concatenated_df.columns = [q_bp_value, q_tur_value]

    return concatenated_df

# Usage example
df = concat_and_rename(results, 'q_tur', 'q_bp')
df_lmp = process_t_data(parameters['LMP'], input=True, col_name='LMP')
df_t = pd.concat([results['T_RM61'], process_t_data(parameters['T_RM61_hourly_max'], input=True, col_name='T_RM61_max')], axis=1)
df_t = pd.concat([df_t, process_t_data(parameters['T_RM61_hourly_min'], input=True, col_name='T_RM61_min')], axis=1)
# Assuming df_t and input_data['T_ramp_down_delta'] are already defined
tmp_min = df_t['T_RM61'] - input_data['T_ramp_down_delta']
tmp_max = df_t['T_RM61'] + input_data['T_ramp_up_delta']
# Shift the 'min' column down by one row
df_t['T_min'] = tmp_min.shift(1)
df_t.loc['t01', 'T_min'] = tmp_min.iloc[-1]
df_t['T_max'] = tmp_max.shift(1)
df_t.loc['t01', 'T_max'] = tmp_max.iloc[-1]
# Cap the 'max' values at 'T_RM61_max'
df_t['T_max'] = df_t[['T_max', 'T_RM61_max']].min(axis=1)
df_t['T_min'] = df_t[['T_min', 'T_RM61_min']].max(axis=1)
df_t['T_min'] = df_t[['T_min', 'T_max']].min(axis=1)


import matplotlib.pyplot as plt
import numpy as np

# Define the plot with subplots
fig, (ax1, ax3) = plt.subplots(nrows=2, ncols=1, figsize=(12, 10), sharex=True)

# Plot the stacked area chart on the primary y-axis of the first subplot
df.plot.area(ax=ax1, alpha=0.6)

# Customizations for the primary y-axis
ax1.set_title('Turbine and Bypass Release', fontsize=15)
ax1.set_ylabel('CFS', fontsize=12)

# Customize the x-ticks for the shared x-axis
ax1.set_xticks(np.arange(0, len(df.index)))
ax1.set_xticklabels(df.index)

# Grid for better visualization
ax1.grid(True, linestyle='--', alpha=0.5)

# Customize the colors for the area plot
# colors = ['#ff9999', '#66b3ff']
colors = ['#ff9999', '#66b3ff']
for i, patch in enumerate(ax1.get_children()[:2]):
    patch.set_color(colors[i])

# Create a secondary y-axis for the first subplot
ax2 = ax1.twinx()

# Plot df_lmp on the secondary y-axis of the first subplot without generating a legend
df_lmp.plot(ax=ax2, color='black', linewidth=2, legend=False)

# Customizations for the secondary y-axis
ax2.set_ylabel('LMP ($/MWh)', fontsize=12)

# Combine legends for the first subplot
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12, title='Categories', title_fontsize='14')

# Plot df_t on the second subplot with specific colors for T_RM61 and T_RM61_max
df_t['T_RM61'].plot(ax=ax3, linewidth=2, color='black', label='T_RM61')
df_t['T_RM61_max'].plot(ax=ax3, linewidth=2, linestyle='--', color='red', label='T_RM61_max')
df_t['T_RM61_min'].plot(ax=ax3, linewidth=2, linestyle='--', color='red', label='T_RM61_min')

# Plot df_t['T_min'] and df_t['T_max']
df_t['T_min'].plot(ax=ax3, linestyle='--', color='green', label='T_min_range')
df_t['T_max'].plot(ax=ax3, linestyle='--', color='green', label='T_max_range')

# Fill the area below the minimum values
fill_below = ax3.fill_between(df_t.index, df_t['T_RM61_min'], y2=df_t['T_RM61_min'].min()-1, color='red', alpha=0.05, edgecolor='black', linestyle='--')
fill_below.set_label('Outside T range')

# Fill the area above the maximum values
fill_above = ax3.fill_between(df_t.index, df_t['T_RM61_max'], y2=df_t['T_RM61_max'].max()+1, color='red', alpha=0.05, edgecolor='black', linestyle='--')

# Fill in the area between 'T_min' and 'T_max' columns
fill_between = ax3.fill_between(df_t.index, df_t['T_min'], df_t['T_max'], color='green', alpha=0.2, edgecolor='black', linestyle='--')
fill_between.set_label('Allowed T ramping range')

# Customizations for the second subplot
ax3.set_title('Temperature Data', fontsize=15)
ax3.set_xlabel('Labels', fontsize=12)
ax3.set_ylabel('Temperature (°C)', fontsize=12)

# Customize the x-ticks for the shared x-axis
ax3.set_xticks(np.arange(0, len(df.index)))
ax3.set_xticklabels(df.index)

# Grid for better visualization
ax3.grid(True, linestyle='--', alpha=0.5)

# Combine legends for the second subplot
lines3, labels3 = ax3.get_legend_handles_labels()
ax3.legend(lines3, labels3, loc='upper left', fontsize=12)

# Show plot
plt.tight_layout()
plt.show()


###### Process delta t