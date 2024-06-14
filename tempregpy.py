"""The Stigler diet problem.

A description of the problem can be found here:
https://en.wikipedia.org/wiki/Stigler_diet.
"""
from ortools.linear_solver import pywraplp
import pandas as pd

# Sets
time = ["t{:02}".format(i) for i in range(1, 25)]
units = ["UnitA"]
power_plant = ["PlantA"]

# Parameters
LMP_values = [46.85, 45.06, 43.83, 42.55, 42.62, 46.61, 76.48, 77.49, 73.64, 68.51, 67.62, 69.34, 69.23, 74.68, 86.84, 97.79, 91.29, 99.07, 103.56, 108.67, 98.73, 91.91, 53.34, 48.72]
T_RM61_hourly_values = [15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 18, 18, 18, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5]
dT_hourly_values = [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]
T_RM61_daily = 15.5
dT_daily = 1.5
T_bp_values = [7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5]
T_tur_values = [15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5]
Demand_values = [1000 for i in range (1, 25)]
Q_tot_daily = 235003
WaterToPowerConversion = 0.0354538
RampUp = 4000
RampDown = 2500
Q_bp_min_values = 0
Q_bp_max_values = 15000
Q_tur_min_values = 2400
Q_tur_max_values = 25000
Q_tot_min_values = 7000
Q_tot_max_values = 12100
T_ramp_up_delta = 1
T_ramp_down_delta = 1
T_RM61_min = 1

LMP = {(t): LMP_values[i] for i, t in enumerate(time)}
T_RM61_hourly = {(t): T_RM61_hourly_values[i] for i, t in enumerate(time)}
dT_hourly = {(t): dT_hourly_values[i] for i, t in enumerate(time)}
T_bp = {(t, u): T_bp_values[i] for i, t in enumerate(time) for u in units}
T_tur = {(t, u): T_tur_values[i] for i, t in enumerate(time) for u in units}
Q_bp_min = {(t, u): Q_bp_min_values for t in time for u in units}
Q_bp_max = {(t, u): Q_bp_max_values for t in time for u in units}
Q_tur_min = {(t, u): Q_tur_min_values for t in time for u in units}
Q_tur_max = {(t, u): Q_tur_max_values for t in time for u in units}
Q_tot_min = {t: Q_tot_min_values for t in time}
Q_tot_max = {t: Q_tot_max_values for t in time}
Demand = {(t): Demand_values[i] for i, t in enumerate(time)}

# Create solver
solver = pywraplp.Solver.CreateSolver('GLOP')

# Variables
q_bp = {(t, u): solver.NumVar(Q_bp_min[t, u], Q_bp_max[t, u], 'q_bp[%s,%s]' % (t, u)) for t in time for u in units}
q_tur = {(t, u): solver.NumVar(Q_tur_min[t, u], Q_tur_max[t, u], 'q_tur[%s,%s]' % (t, u)) for t in time for u in units}
q_tot = {(t, u): solver.NumVar(Q_tot_min[t], Q_tot_max[t], 'q_tot[%s,%s]' % (t, u)) for t in time for u in units}

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
        constraints.append(solver.Add(q_bp[t, u] + q_tur[t, u] == q_tot[t, u]))

# Add constraint for total daily release
constraint_id_main.append('Total daily release')
constraint_id_unit.append(f'')
constraint_id_time.append(f'')
constraints.append(solver.Add(sum(q_tot[t, u] for u in units for t in time) == Q_tot_daily))

# Add constraints for maximum average daily temperature
constraint_id_main.append(f'Maximum average daily temperature')
constraint_id_unit.append(f'')
constraint_id_time.append(f'')
constraints.append(
    solver.Add(sum(q_bp[t, u] * T_bp[t, u] + q_tur[t, u] * T_tur[t, u] for u in units for t in time) <=
               (T_RM61_daily - dT_daily) * sum(q_tot[t, u] for u in units for t in time)))

# Add constraints for maximum hourly temperature
for t in time:
    constraint_id_main.append(f'Maximum hourly temperature')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(solver.Add(sum(q_bp[t, u] * T_bp[t, u] + q_tur[t, u] * T_tur[t, u] for u in units) <=
                                  (T_RM61_hourly[t] - dT_hourly[t]) * sum(q_tot[t, u] for u in units)))

# Add constraints for minimum hourly temperature
for t in time:
    constraint_id_main.append(f'Minimum hourly temperature')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(solver.Add(sum(q_bp[t, u] * T_bp[t, u] + q_tur[t, u] * T_tur[t, u] for u in units) >=
                                  (T_RM61_hourly[t] - dT_hourly[t]-T_RM61_min) * sum(q_tot[t, u] for u in units)))

# Add constraints for power balance
for t in time:
    constraint_id_main.append(f'Demand Balance')
    constraint_id_unit.append(f'')
    constraint_id_time.append(f'{t}')
    constraints.append(solver.Add(Demand[t] - sum(q_tur[t, u] * WaterToPowerConversion for u in units) >= 0))

for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        # Add ramp up constraints
        # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
        if i == 0:
            constraint_id_main.append(f'Initial ramp up constraint')
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            constraints.append(solver.Add(q_tot[time[0], u] - q_tot[time[-1], u] <= RampUp))
        else:
            constraint_id_main.append(f'Ramp up constraint')
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            constraints.append(solver.Add(q_tot[t, u] - q_tot[prev_t, u] <= RampUp))

for u in units:
    for i in range(len(time)):
        t = time[i]
        prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
        if i == 0:
            constraint_id_main.append(f'Initial ramp down constraint')
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            constraints.append(solver.Add(q_tot[time[-1], u] - q_tot[time[0], u] <= RampDown))
        else:
            constraint_id_main.append(f'Ramp down constraint')
            constraint_id_unit.append(f'{u}')
            constraint_id_time.append(f'{t}')
            constraints.append(solver.Add(q_tot[prev_t, u] - q_tot[t, u] <= RampDown))

# #Temperature ramp up delta
# for i in range(len(time)):
#     t = time[i]
#     prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
#     if i == 0:
#         constraint_id_main.append(f'Initial temp delta hourly ramp up max')
#         constraint_id_unit.append(f'')
#         constraint_id_time.append(f'{t}')
#         constraints.append(solver.Add(sum(q_bp[time[0], u] * T_bp[time[0], u] + q_tur[time[0], u] * T_tur[time[0], u] -
#                                       (q_bp[time[-1], u] * T_bp[time[-1], u] + q_tur[time[-1], u] * T_tur[time[-1], u]) for u in units) <=
#                                       T_ramp_up_delta * sum(q_tot[time[-1], u] for u in units)))
#     else:
#         constraint_id_main.append(f'Temp delta hourly ramp up max')
#         constraint_id_unit.append(f'')
#         constraint_id_time.append(f'{t}')
#         constraints.append(solver.Add(sum(q_bp[t, u] * T_bp[t, u] + q_tur[t, u] * T_tur[t, u] -
#                                       (q_bp[prev_t, u] * T_bp[prev_t, u] + q_tur[prev_t, u] * T_tur[prev_t, u]) for u in units) <=
#                                       T_ramp_up_delta * sum(q_tot[prev_t, u] for u in units)))
#
# #Temperature ramp down delta
# for i in range(len(time)):
#     t = time[i]
#     prev_t = time[i - 1] if i > 0 else time[-1]  # Handling wrap-around
#     if i == 0:
#         constraint_id_main.append(f'Initial temp delta hourly ramp down max')
#         constraint_id_unit.append(f'')
#         constraint_id_time.append(f'{t}')
#         constraints.append(solver.Add(sum(q_bp[time[0], u] * T_bp[time[0], u] + q_tur[time[0], u] * T_tur[time[0], u] -
#                                       (q_bp[time[-1], u] * T_bp[time[-1], u] + q_tur[time[-1], u] * T_tur[time[-1], u]) for u in units) >=
#                                       -T_ramp_down_delta * sum(q_tot[time[-1], u] for u in units)))
#     else:
#         constraint_id_main.append(f'Temp delta hourly ramp down max')
#         constraint_id_unit.append(f'')
#         constraint_id_time.append(f'{t}')
#         constraints.append(solver.Add(sum(q_bp[t, u] * T_bp[t, u] + q_tur[t, u] * T_tur[t, u] -
#                                       (q_bp[prev_t, u] * T_bp[prev_t, u] + q_tur[prev_t, u] * T_tur[prev_t, u]) for u in units) >=
#                                       -T_ramp_down_delta * sum(q_tot[prev_t, u] for u in units)))



# Objective
objective = solver.Objective()
for u in units:
    for t in time:
        objective.SetCoefficient(q_tur[t, u], LMP[t]*WaterToPowerConversion)

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
    results['q_tur'] = process_u_t_data(q_tur)
    results['q_bp'] = process_u_t_data(q_bp)
    results['q_tot'] = process_u_t_data(q_tot)
    results['T_dam'] = (results['q_tur'] * process_u_t_data(T_tur, input=True) + results['q_bp'] * process_u_t_data(T_bp, input=True)) / results['q_tot']
    results['T_RM61'] = results['T_dam'].T + process_t_data(dT_hourly, input=True,col_name='UnitA')
    results['T_RM61'].columns = ['T_RM61']
    results['Dual Values'] = export_dual_values(constraints, constraint_id_main, constraint_id_unit, constraint_id_time)

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
df_lmp = process_t_data(LMP, input=True, col_name='LMP')
df_t = pd.concat([results['T_RM61'], process_t_data(T_RM61_hourly, input=True,col_name='T_RM61_max')], axis=1)
# Assuming df_t and T_ramp_down_delta are already defined
tmp_min = df_t['T_RM61'] - T_ramp_down_delta
tmp_max = df_t['T_RM61'] + T_ramp_up_delta
# Shift the 'min' column down by one row
df_t['T_min'] = tmp_min.shift(1)
df_t.loc['t01', 'T_min'] = tmp_min.iloc[-1]
df_t['T_max'] = tmp_max.shift(1)
df_t.loc['t01', 'T_max'] = tmp_max.iloc[-1]
# Cap the 'max' values at 'T_RM61_max'
df_t['T_max'] = df_t[['T_max', 'T_RM61_max']].min(axis=1)


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

# Plot df_t on the second subplot
df_t[['T_RM61', 'T_RM61_max']].plot(ax=ax3, linewidth=2, style=['-', '--'])

# Plot df_t['T_min'] and df_t['T_max']
df_t['T_min'].plot(ax=ax3, linestyle='--', color='green', label='T_min')
df_t['T_max'].plot(ax=ax3, linestyle='--', color='red', label='T_max')

# Fill in the area between 'T_min' and 'T_max' columns
fill_between = ax3.fill_between(df_t.index, df_t['T_min'], df_t['T_max'], color='gray', alpha=0.2, edgecolor='black', linestyle='--')
fill_between.set_label('Allowed T range')

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


#####################################################################
# 3d contur plot
########################

import numpy as np
import matplotlib.pyplot as plt
import  matplotlib.gridspec as gridspec
from scipy.spatial import ConvexHull

x = np.linspace(Q_tur_min_values, Q_tur_max_values, 10, endpoint=True)
y = np.linspace(Q_bp_min_values, Q_bp_max_values, 10, endpoint=True)

# Generate the meshgrid for the pairs of equal variables
Q_tur, Q_bp, Q_tur1, Q_bp1 = np.meshgrid(x, y, x, y, indexing='ij')

# Example function to evaluate
Q_tot = Q_tur + Q_bp
Q_tot1 = Q_tur1 + Q_bp1
X = Q_bp * Q_tur1
Y = Q_tur * Q_bp1
Z = Q_tot * Q_tot1

# Flatten the arrays for convex hull computation
points_X = np.c_[Q_bp.flatten(), Q_tur1.flatten(), X.flatten()]
points_Y = np.c_[Q_tur.flatten(), Q_bp1.flatten(), Y.flatten()]
points_Z = np.c_[Q_tot.flatten(), Q_tot1.flatten(), Z.flatten()]


# Function to compute convex hull, plane equations, and centroids
# Function to compute convex hull, plane equations, centroids, and inequality signs
def compute_hull_and_planes(points):
    hull = ConvexHull(points)

    plane_equations = []
    inequality_signs = []
    simplex_centroids = []

    # Calculate centroid of the points as a reference point
    centroid = np.mean(points, axis=0)

    # Function to calculate the plane equation from three points and normalize it
    def normalized_plane_equation(p1, p2, p3):
        v1 = p2 - p1
        v2 = p3 - p1
        normal = np.cross(v1, v2)
        a, b, c = normal
        d = np.dot(normal, p1)
        norm = np.linalg.norm(normal)
        a, b, c, d = a / norm, b / norm, c / norm, d / norm
        return a, b, c, d

    # Loop over the simplices (facets) and compute the normalized plane equations
    for simplex in hull.simplices:
        p1 = points[simplex[0]]
        p2 = points[simplex[1]]
        p3 = points[simplex[2]]
        a, b, c, d = normalized_plane_equation(p1, p2, p3)
        plane_equations.append((a, b, c, d))
        # Determine inequality direction
        value_at_centroid = a * centroid[0] + b * centroid[1] + c * centroid[2] - d
        if value_at_centroid < 0:
            inequality_signs.append("<=")
        else:
            inequality_signs.append(">=")
        # Calculate centroid of the simplex
        simplex_centroid = np.mean([p1, p2, p3], axis=0)
        simplex_centroids.append(simplex_centroid)

    return hull, plane_equations, inequality_signs, simplex_centroids


# Compute hulls and planes for X, Y, Z
hull_X, plane_eqs_X, ineq_sign_X, centroids_X = compute_hull_and_planes(points_X)
hull_Y, plane_eqs_Y, ineq_sign_Y, centroids_Y = compute_hull_and_planes(points_Y)
hull_Z, plane_eqs_Z, ineq_sign_Z, centroids_Z = compute_hull_and_planes(points_Z)

print("Plane Equations for X = Q_bp * Q_tur1:")
for i, ((a, b, c, d), sign) in enumerate(zip(plane_eqs_X, ineq_sign_X)):
    print(f"Plane {i}: {a:.3f}x + {b:.3f}y + {c:.3f}z {sign} {d:.3f}")

print("\nPlane Equations for Y = Q_tur * Q_bp1:")
for i, ((a, b, c, d), sign) in enumerate(zip(plane_eqs_Y, ineq_sign_Y)):
    print(f"Plane {i}: {a:.3f}x + {b:.3f}y + {c:.3f}z {sign} {d:.3f}")

print("\nPlane Equations for Z = Q_tot * Q_tot1:")
for i, ((a, b, c, d), sign) in enumerate(zip(plane_eqs_Z, ineq_sign_Z)):
    print(f"Plane {i}: {a:.3f}x + {b:.3f}y + {c:.3f}z {sign} {d:.3f}")

# Create a 2-column, 2-row grid of subplots
fig = plt.figure(figsize=(14, 12))
gs = gridspec.GridSpec(2, 2, figure=fig)

# Assign specific axes to variables
ax1 = fig.add_subplot(gs[0, 0], projection='3d')  # First row, first column
ax2 = fig.add_subplot(gs[0, 1], projection='3d')  # First row, second column
ax3 = fig.add_subplot(gs[1, 0], projection='3d')  # Second row, first column
ax4 = fig.add_subplot(gs[1, 1], projection='3d')  # Second row, second column

# Plot for X = Q_bp * Q_tur1
ax3.scatter(points_X[:, 0], points_X[:, 1], points_X[:, 2], c='b', marker='o', label='Data points')
for simplex in hull_X.simplices:
    simplex_points = points_X[simplex]
    ax3.plot_trisurf(simplex_points[:, 0], simplex_points[:, 1], simplex_points[:, 2], color='r', alpha=0.3, label='Convex Hull')
ax3.set_xlabel('$Q_{bp,t}$')
ax3.set_ylabel('$Q_{tur,t-1}$')
ax3.set_zlabel('$Q_{bp,t} \cdot Q_{tur,t-1}$')
ax3.set_title('Scatter plot with Convex Hull for $X$')
ax3.invert_xaxis()

# Plot for Z = Q_tot * Q_tot1
ax4.scatter(points_Z[:, 0], points_Z[:, 1], points_Z[:, 2], c='b', marker='o', label='Data points')
for simplex in hull_Z.simplices:
    simplex_points = points_Z[simplex]
    ax4.plot_trisurf(simplex_points[:, 0], simplex_points[:, 1], simplex_points[:, 2], color='r', alpha=0.3, label='Convex Hull')
ax4.set_xlabel('$Q_{tot,t}$')
ax4.set_ylabel('$Q_{tot,t-1}$')
ax4.set_zlabel('$Q_{tot,t} \cdot Q_{tot,t-1}$')
ax4.set_title('Scatter plot with Convex Hull for $Z$')
ax4.invert_xaxis()

# Meshgrid data for surface plots
Q_bp_mesh, Q_tur_mesh = np.meshgrid(x, y)
X_mesh = Q_bp_mesh * Q_tur_mesh
Q_tot_mesh, Q_tot1_mesh = np.meshgrid(x + y, x + y)
Z_mesh = Q_tot_mesh * Q_tot1_mesh

# Surface plot for X = Q_bp * Q_tur1
surf_real1 = ax1.plot_surface(Q_bp_mesh, Q_tur_mesh, X_mesh, cmap='viridis', label='Surface')
ax1.set_xlabel('$Q_{bp,t}$')
ax1.set_ylabel('$Q_{tur,t-1}$')
ax1.set_zlabel('$Q_{bp,t} \cdot Q_{tur,t-1}$')
ax1.set_title('Surface plot for $X$')
ax1.invert_xaxis()
# cbar1 = fig.colorbar(surf_real1, ax=ax1, orientation='horizontal', shrink=0.5, aspect=30, pad=0)
# cbar1.set_label('Surface Intensity')

# Surface plot for Z = Q_tot * Q_tot1
surf_real3 = ax2.plot_surface(Q_tot_mesh, Q_tot1_mesh, Z_mesh, cmap='viridis', label='Surface')
ax2.set_xlabel('$Q_{tot,t}$')
ax2.set_ylabel('$Q_{tot,t-1}$')
ax2.set_zlabel('$Q_{tot,t} \cdot Q_{tot,t-1}$')
ax2.set_title('Surface plot for $Z$')
ax2.invert_xaxis()
# cbar2 = fig.colorbar(surf_real3, ax=ax2, orientation='horizontal', shrink=0.5, aspect=30, pad=0)
# cbar2.set_label('Surface Intensity')

# Set layout and save the figure
plt.tight_layout()
plt.savefig('Qbp-Qtur-T.png', dpi=300, bbox_inches='tight')
plt.show()

