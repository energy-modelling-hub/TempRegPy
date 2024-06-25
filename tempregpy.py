"""The Stigler diet problem.

A description of the problem can be found here:
https://en.wikipedia.org/wiki/Stigler_diet.
"""
from ortools.linear_solver import pywraplp
from tempregpy import *
import pandas as pd
import os
import sys

# Load the Excel file
file_path = './TempRegPy.xlsx'
full_path = os.path.abspath(file_path)

# Log the file name and full path
logger.info(f'Reading Excel file: {os.path.basename(file_path)}')
logger.info(f'Full path: {full_path}')

try:
    # Load the Excel file
    excel_data = pd.ExcelFile(file_path)
    logger.info('File has been successfully read.')
    # Parse the relevant sheet
    try:
        df = excel_data.parse('Inputs')
        logger.info('Inputs have been succesfully parsed')
    except Exception as e1:
        logger.info('Not able to parse Inputs')
        sys.exit(1)
except Exception as e:
    logger.error(f'Failed to read the file. Error: {e}')
    sys.exit(1)

# Initialize the input_data dictionary
input_data = {}
input_data['sim_folder'] = df.loc[df['Python Variable Names'] == 'sim_folder', 'Single input'].values[0]
input_data['cnstr_bp_ramp'] = df.loc[df['Python Variable Names'] == 'cnstr_bp_ramp', 'Single input'].values[0]
input_data['cnstr_tur_ramp'] = df.loc[df['Python Variable Names'] == 'cnstr_tur_ramp', 'Single input'].values[0]
input_data['cnstr_tot_ramp'] = df.loc[df['Python Variable Names'] == 'cnstr_tot_ramp', 'Single input'].values[0]
input_data['cnstr_temp_t01t24'] = df.loc[df['Python Variable Names'] == 'cnstr_temp_t01t24', 'Single input'].values[0]
input_data['cnstr_bp_t01t24'] = df.loc[df['Python Variable Names'] == 'cnstr_bp_t01t24', 'Single input'].values[0]
input_data['cnstr_tur_t01t24'] = df.loc[df['Python Variable Names'] == 'cnstr_tur_t01t24', 'Single input'].values[0]
input_data['cnstr_tot_t01t24'] = df.loc[df['Python Variable Names'] == 'cnstr_tot_t01t24', 'Single input'].values[0]
input_data['cnstr_oper_range'] = df.loc[df['Python Variable Names'] == 'cnstr_oper_range', 'Single input'].values[0]
input_data['cnstr_temp_convex_hull'] = df.loc[df['Python Variable Names'] == 'cnstr_temp_convex_hull', 'Single input'].values[0]
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

if input_data['cnstr_temp_convex_hull'] is True:
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

if input_data['cnstr_temp_t01t24'] is True:
    logger.warning(
        'Temperature for H01 == H24 constraints included in the optimization, might be in conflict with turbine, bypass and total release at H01 == H24')
    constraint_id_main.append(f'Temperature t01 = t24')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'')
    constraints.append(solver.Add(sum(variables['q_bp'][time[0], u] * parameters['T_bp'][time[0], u] + variables['q_tur'][time[0], u] * parameters['T_tur'][time[0], u] - (parameters['T_RM61_hourly_max'][time[0]] - parameters['dT_hourly'][time[0]])*variables['q_tot'][time[0], u] for u in units) ==
                                  sum(variables['q_bp'][time[-1], u] * parameters['T_bp'][time[-1], u] + variables['q_tur'][time[-1], u] * parameters['T_tur'][time[-1], u] - (parameters['T_RM61_hourly_max'][time[-1]] - parameters['dT_hourly'][time[-1]])*variables['q_tot'][time[-1], u] for u in units)))

if input_data['cnstr_bp_t01t24'] is True:
    logger.warning(
        'Bypass release for H01 == H24 constraints included in the optimization, might be in conflict with temperature at H01 == H24')
    constraint_id_main.append(f'q_bp t01 = t24')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'')
    constraints.append(solver.Add(sum(variables['q_bp'][time[0], u] for u in units) == sum(variables['q_bp'][time[-1], u] for u in units)))

if input_data['cnstr_tur_t01t24'] is True:
    logger.warning(
        'Turbine release for H01 == H24 constraints included in the optimization, might be in conflict with temperature at H01 == H24')
    constraint_id_main.append(f'q_tur t01 = t24')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'')
    constraints.append(solver.Add(sum(variables['q_tur'][time[0], u] for u in units) == sum(variables['q_tur'][time[-1], u] for u in units)))

if input_data['cnstr_tot_t01t24'] is True:
    logger.warning('Total release for H01 == H24 constraints included in the optimization, might be in conflict with temperature at H01 == H24')
    constraint_id_main.append(f'q_tot t01 = t24')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'')
    constraints.append(solver.Add(sum(variables['q_tot'][time[0], u] for u in units) == sum(variables['q_tot'][time[-1], u] for u in units)))

if input_data['cnstr_oper_range'] is True:
    logger.info('Maximum daily operating range constraints included in the optimization')
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

if input_data['cnstr_bp_ramp'] is True:
    logger.info('Bypass release ramping constraints included in the optimization')
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

if input_data['cnstr_tur_ramp'] is True:
    logger.info('Turbine release ramping constraints included in the optimization')
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

if input_data['cnstr_tot_ramp']:
    logger.info('Total release ramping constraints included in the optimization')
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
if input_data['cnstr_temp_convex_hull'] is True:
    logger.info('Convex hull temperature ramping approximation constraints included in the optimization')
    for u in units:
        for t in time:
            constraint_id_main.append(f'Temperature ramp up constraint')
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            constraints.append(solver.Add((variables['q_bp_t_tur_t1'][t, u] - variables['q_tur_t_bp_t1'][t, u])*(parameters['T_bp'][t, u] - parameters['T_tur'][t, u]) <=
                                          input_data['T_ramp_up_delta'] * variables['q_tot_t_tot_t1'][t, u]))

    for u in units:
        for t in time:
            constraint_id_main.append(f'Temperature ramp down constraint')
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

# Check if the problem has an optimal solution
if status == pywraplp.Solver.OPTIMAL:
    logger.info('Objective value = ' + str(objective.Value()))
    results = {}
    results['Objective Value'] = objective.Value()
    results['q_tot_min'] = process_single_index(variables['q_tot_min'], units)
    results['q_tur'] = process_double_index(variables['q_tur'], time, units)
    results['q_bp'] = process_double_index(variables['q_bp'], time, units)
    results['q_tot'] = process_double_index(variables['q_tot'], time, units)
    results['p_tur'] = process_double_index(variables['p_tur'], time, units)
    results['q_bp_t_tur_t1'] = process_double_index(variables['q_bp_t_tur_t1'], time, units)
    results['q_tur_t_bp_t1'] = process_double_index(variables['q_tur_t_bp_t1'], time, units)
    results['q_tot_t_tot_t1'] = process_double_index(variables['q_tot_t_tot_t1'], time, units)
    results['q_bp_ramp_up'] = process_double_index(variables['q_bp_ramp_up'], time, units)
    results['q_bp_ramp_down'] = process_double_index(variables['q_bp_ramp_down'], time, units)
    results['q_tur_ramp_up'] = process_double_index(variables['q_tur_ramp_up'], time, units)
    results['q_tur_ramp_down'] = process_double_index(variables['q_tur_ramp_down'], time, units)
    results['q_tot_ramp_up'] = process_double_index(variables['q_tot_ramp_up'], time, units)
    results['q_tot_ramp_down'] = process_double_index(variables['q_tot_ramp_down'], time, units)
    results['T_dam'] = (results['q_tur'] * process_double_index(parameters['T_tur'], time, units, input=True) + results['q_bp'] * process_double_index(parameters['T_bp'], time, units, input=True)) / results['q_tot']
    results['T_RM61'] = results['T_dam'].T + process_single_index(parameters['dT_hourly'], time, input=True, col_name='UnitA')
    results['T_RM61'].columns = ['T_RM61']
    results['Dual Values'] = export_dual_values(constraints, constraint_id_main, constraint_id_unit, constraint_id_time)
    results['T_dam'] = results['T_dam'].T
    results['T_dam'].columns = ['T_dam']


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
    df_dispatch = concat_and_rename(results, 'q_tur', 'q_bp')
    df_lmp = process_single_index(parameters['LMP'], time, input=True, col_name='LMP')
    # Concatenate initial dataframes
    results['Temperature_summary'] = pd.concat([
        results['T_RM61'],
        process_single_index(parameters['T_RM61_hourly_max'], time, input=True, col_name='T_RM61_max'),
        process_single_index(parameters['T_RM61_hourly_min'], time, input=True, col_name='T_RM61_min')
    ], axis=1)

    # Calculate 'T_min' and 'T_max'
    results['Temperature_summary']['T_min'] = (results['Temperature_summary']['T_RM61'] - input_data['T_ramp_down_delta']).shift(1)
    results['Temperature_summary'].loc['t01', 'T_min'] = (results['Temperature_summary']['T_RM61'] - input_data['T_ramp_down_delta']).iloc[-1]

    results['Temperature_summary']['T_max'] = (results['Temperature_summary']['T_RM61'] + input_data['T_ramp_up_delta']).shift(1)
    results['Temperature_summary'].loc['t01', 'T_max'] = (results['Temperature_summary']['T_RM61'] + input_data['T_ramp_up_delta']).iloc[-1]

    # Cap 'T_max' and 'T_min' values
    results['Temperature_summary']['T_max'] = results['Temperature_summary'][['T_max', 'T_RM61_max']].min(axis=1)
    results['Temperature_summary']['T_min'] = results['Temperature_summary'][['T_min', 'T_RM61_min']].max(axis=1)

    # Concatenate additional results and add 'd_T' column
    results['Temperature_summary'] = pd.concat([results['Temperature_summary'], results['T_dam']], axis=1)
    results['Temperature_summary']['d_T'] = process_single_index(parameters['dT_hourly'], time, input=True, col_name='UnitA')

    # Determine the directory where the Excel file is located
    base_directory = os.path.dirname(file_path)

    # Create the "results" folder in the same directory as the Excel file
    results_folder_path = os.path.join(base_directory, 'Results')
    os.makedirs(results_folder_path, exist_ok=True)

    # Create the simulation folder inside the "results" folder
    simulation_folder_path = os.path.join(results_folder_path, input_data['sim_folder'])

    plot_temperature_analysis(df_dispatch, results['Temperature_summary'], df_lmp, save_fig=True, fig_name=simulation_folder_path + '\\plot')

    # Check if the folder already exists
    if os.path.exists(simulation_folder_path):
        logger.warning("The old simulation will be overwritten.")
    else:
        # Create the folder
        try:
            os.makedirs(simulation_folder_path)
            logger.info(f"The folder '{simulation_folder_path}' has been created.")
        except Exception as e:
            logger.error(f"Failed to create folder '{simulation_folder_path}'. Error: {e}")
            sys.exit(1)

    # Export results to a file
    results_file_path = os.path.join(simulation_folder_path, 'optimization_results.txt')
    try:
        with open(results_file_path, 'w') as f:
            logger.info(f'Writing results to: {results_file_path}')
            f.write('Results:\n')

            for key, value in results.items():
                if isinstance(value, pd.DataFrame):
                    f.write(f'{key}:\n{value.to_string()}\n\n')
                else:
                    f.write(f'{key}: {value}\n')
    except Exception as e:
        logger.error(f"Failed to write results to file '{results_file_path}'. Error: {e}")
        sys.exit(1)

else:
    logger.error('The problem does not have an optimal solution.')

copy_file_to_destination('TempRegPy\\app.log', simulation_folder_path)


for key, value in results.items():
    if isinstance(value, pd.DataFrame):
        value.to_csv(f'{simulation_folder_path+'\\'}{key}.csv', index=False)
    else:
        with open(f'{simulation_folder_path+'\\'}{key}.csv', 'w') as f:
            f.write(str(value))
