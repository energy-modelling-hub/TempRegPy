import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.spatial import ConvexHull
import pandas as pd
from tempregpy.logging_config import *
import sys
import os
from .constants import *


class HullComputation:
    def __init__(self, points, label):
        self.points = points
        self.label = label
        self.hull, self.plane_equations, self.inequality_signs, self.simplex_centroids = self.compute_hull_and_planes()

    def compute_hull_and_planes(self):
        hull = ConvexHull(self.points)
        plane_equations = []
        inequality_signs = []
        simplex_centroids = []
        centroid = np.mean(self.points, axis=0)

        def normalized_plane_equation(point1, point2, point3):
            v1 = point2 - point1
            v2 = point3 - point1
            normal = np.cross(v1, v2)
            coef_a, coef_b, coef_c = normal
            coef_d = np.dot(normal, point1)
            norm = np.linalg.norm(normal)
            return coef_a / norm, coef_b / norm, coef_c / norm, coef_d / norm

        for simplex in hull.simplices:
            p1, p2, p3 = self.points[simplex]
            a, b, c, d = normalized_plane_equation(p1, p2, p3)
            plane_equations.append((a, b, c, d))
            value_at_centroid = a * centroid[0] + b * centroid[1] + c * centroid[2] - d
            inequality_signs.append("<=" if value_at_centroid < 0 else ">=")
            simplex_centroids.append(np.mean([p1, p2, p3], axis=0))

        return hull, plane_equations, inequality_signs, simplex_centroids

    def print_plane_equations(self):
        label = self.label
        logger.info(f"Plane Equations for {label}:")
        for i, ((a, b, c, d), sign) in enumerate(zip(self.plane_equations, self.inequality_signs)):
            logger.info(f"Plane {i}: {a:.3f}x + {b:.3f}y + {c:.3f}z {sign} {d:.3f}")


class DataGenerator:
    def __init__(self, Q_tur_min, Q_tur_max, Q_bp_min, Q_bp_max, Q_tot_min, Q_tot_max):
        self.Q_tur_min = Q_tur_min
        self.Q_tur_max = Q_tur_max
        self.Q_bp_min = Q_bp_min
        self.Q_bp_max = Q_bp_max
        self.Q_tot_min = Q_tot_min
        self.Q_tot_max = Q_tot_max
        self.generate_data()

    def generate_data(self):
        x = np.linspace(self.Q_tur_min, self.Q_tur_max, 4, endpoint=True)
        y = np.linspace(self.Q_bp_min, self.Q_bp_max, 4, endpoint=True)
        z = np.linspace(self.Q_tot_min, self.Q_tot_max, 4, endpoint=True)
        Q_bp, Q_tur1 = np.meshgrid(y, x, indexing='ij')
        Q_tur, Q_bp1 = np.meshgrid(x, y, indexing='ij')
        Q_tot, Q_tot1 = np.meshgrid(z, z, indexing='ij')

        self.points_X = np.c_[Q_bp.flatten(), Q_tur1.flatten(), (Q_bp * Q_tur1).flatten()]
        self.points_Y = np.c_[Q_tur.flatten(), Q_bp1.flatten(), (Q_tur * Q_bp1).flatten()]
        self.points_Z = np.c_[Q_tot.flatten(), Q_tot1.flatten(), (Q_tot * Q_tot1).flatten()]

        self.Q_bp_mesh, self.Q_tur_mesh = np.meshgrid(y, x)
        self.X_mesh = self.Q_bp_mesh * self.Q_tur_mesh
        self.Q_tot_mesh, self.Q_tot1_mesh = np.meshgrid(z, z)
        self.Z_mesh = self.Q_tot_mesh * self.Q_tot1_mesh


class Plotter:
    def __init__(self, data_gen, hull_X, hull_Y, hull_Z):
        self.data_gen = data_gen
        self.hull_X = hull_X
        self.hull_Y = hull_Y
        self.hull_Z = hull_Z
        self.create_plots()

    def create_plots(self):
        fig = plt.figure(figsize=(14, 12))
        gs = gridspec.GridSpec(2, 2, figure=fig)
        ax1 = fig.add_subplot(gs[0, 0], projection='3d')
        ax2 = fig.add_subplot(gs[0, 1], projection='3d')
        ax3 = fig.add_subplot(gs[1, 0], projection='3d')
        ax4 = fig.add_subplot(gs[1, 1], projection='3d')

        self.plot_scatter_and_hull(ax3, self.data_gen.points_X, self.hull_X, '$Q_{bp,t}$', '$Q_{tur,t-1}$', '$Q_{bp,t} \\cdot Q_{tur,t-1}$', 'Scatter plot with Convex Hull for $X$')
        self.plot_scatter_and_hull(ax4, self.data_gen.points_Z, self.hull_Z, '$Q_{tot,t}$', '$Q_{tot,t-1}$', '$Q_{tot,t} \\cdot Q_{tot,t-1}$', 'Scatter plot with Convex Hull for $Z$')
        self.plot_surface(ax1, self.data_gen.Q_bp_mesh, self.data_gen.Q_tur_mesh, self.data_gen.X_mesh, '$Q_{bp,t}$', '$Q_{tur,t-1}$', '$Q_{bp,t} \\cdot Q_{tur,t-1}$', 'Surface plot for $X$')
        self.plot_surface(ax2, self.data_gen.Q_tot_mesh, self.data_gen.Q_tot1_mesh, self.data_gen.Z_mesh, '$Q_{tot,t}$', '$Q_{tot,t-1}$', '$Q_{tot,t} \\cdot Q_{tot,t-1}$', 'Surface plot for $Z$')

        plt.tight_layout()
        # plt.savefig('Qbp-Qtur-T.png', dpi=300, bbox_inches='tight')
        # plt.show()

    def plot_scatter_and_hull(self, ax, points, hull, xlabel, ylabel, zlabel, title):
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], c='b', marker='o', label='Data points')
        for simplex in hull.hull.simplices:
            simplex_points = points[simplex]
            ax.plot_trisurf(simplex_points[:, 0], simplex_points[:, 1], simplex_points[:, 2], color='r', alpha=0.3, label='Convex Hull')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_zlabel(zlabel)
        ax.set_title(title)
        ax.invert_xaxis()

    def plot_surface(self, ax, X, Y, Z, xlabel, ylabel, zlabel, title):
        ax.plot_surface(X, Y, Z, cmap='viridis', label='Surface')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_zlabel(zlabel)
        ax.set_title(title)
        ax.invert_xaxis()


def process_double_index(variable, idx1, idx2, input=False):
    if input is False:
        data = {(t, u): variable[t, u].solution_value() for t in idx1 for u in idx2}
    else:
        data = {(t, u): variable[t, u] for t in idx1 for u in idx2}
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

def process_single_index(variable, idx, input=False, col_name=''):
    if input is False:
        data = {(t): variable[t].solution_value() for t in idx}
    else:
        data = {(t): variable[t] for t in idx}
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


def load_config(file_path):
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
            config = excel_data.parse('Inputs')
            logger.info('Inputs have been succesfully parsed')
            par_name = 'Python Variable Names'
            input_type = 'Single input'

            # Initialize the input_data dictionary
            inputs = {}
            inputs['file_path'] = file_path

            # Define the list of keys to extract
            keys = [
                'sim_folder', 'plt_show', 'cnstr_bp_ramp', 'cnstr_tur_ramp', 'cnstr_tot_ramp',
                'cnstr_temp_t01t24', 'cnstr_bp_t01t24', 'cnstr_tur_t01t24', 'cnstr_tot_t01t24',
                'cnstr_oper_range', 'cnstr_temp_convex_hull', 'Q_tot_daily', 'T_ramp_up_delta', 'T_ramp_down_delta',
                'T_RM61_daily', 'dT_daily'
            ]

            # Loop through each key and extract the corresponding value
            for key in keys:
                inputs[key] = config.loc[config[par_name] == key, input_type].values[0]

            keys_with_conversion = {
                'Q_max_daily_change': cfs_to_af,
                'Q_bp_ramp_down_max': cfs_to_af,
                'Q_bp_ramp_up_max': cfs_to_af,
                'Q_tur_ramp_down_max': cfs_to_af,
                'Q_tur_ramp_up_max': cfs_to_af,
                'Q_tot_ramp_up_max': cfs_to_af,
                'Q_tot_ramp_down_max': cfs_to_af,
                'WaterToPowerConversion': 1 / cfs_to_af
            }

            # Loop through each key and apply the corresponding conversion factor
            for key, factor in keys_with_conversion.items():
                inputs[key] = config.loc[config[par_name] == key, input_type].values[0] * factor

            # Hourly values
            hours = [f'H{i:02}' for i in range(1, 25)]

            for var in ['Q_bp_min_values', 'Q_bp_max_values', 'Q_tur_min_values', 'Q_tur_max_values',
                        'Q_tot_min_values', 'Q_tot_max_values']:
                inputs[var] = (config.loc[config[par_name] == var, hours].values*cfs_to_af).flatten().tolist() #CFS->AF

            for var in ['T_bp_values', 'T_tur_values', 'T_RM61_hourly_max_values', 'T_RM61_hourly_min_values',
                        'dT_hourly_values', 'LMP_values', 'Demand_values', 'P_tur_min_values', 'P_tur_max_values']:
                inputs[var] = config.loc[config[par_name] == var, hours].values.flatten().tolist()

            # Penalty costs
            for var in ['C_bp_ramp_up', 'C_bp_ramp_down', 'C_tur_ramp_up', 'C_tur_ramp_down', 'C_tot_ramp_up',
                        'C_tot_ramp_down']:
                inputs[var] = config.loc[config[par_name] == var, input_type].values[0]/cfs_to_af #CFS->AF

            return inputs
        except Exception as e:
            logger.error(f'Not able to parse Inputs. Error: {e}')
            sys.exit(1)
    except Exception as e:
        logger.error(f'Failed to read the file. Error: {e}')
        sys.exit(1)
