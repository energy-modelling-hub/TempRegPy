import sys
import enum

import numpy as np
import pandas as pd

from ..logging_config import *
from ..model.constants import *
from ..model.rough_zones import *
from tempregpy.model.utils import process_dates_to_groups

from tempregpy.model.functions import (
    HullComputation,
    DataGenerator,
    Plotter,
    gauge_hulls,
    gauge_hulls_time,
    process_double_index,
    process_single_index,
    export_dual_values,
    initialize_inputs,
    initialize_inputs_with_index,
    initialize_inputs_with_conversion,
)


@enum.unique
class DayType(enum.Enum):
    WEEKDAY = "WEEKDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
    HOLIDAY = "HOLIDAY"


def map_date_to_day_type(date, holidays):
    if date in holidays:
        return DayType.HOLIDAY
    elif date.weekday() < 5:  # Monday to Friday
        return DayType.WEEKDAY
    elif date.weekday() == 5:  # Saturday
        return DayType.SATURDAY
    else:  # Sunday
        return DayType.SUNDAY


def load_inputs_from_excel(config):
    try:
        logger.info('Inputs have been succesfully parsed')

        par_name = 'Python Variable Names'
        input_type = 'Single input'

        # Initialize the input_data dictionary
        inputs = {}
        inputs['version'] = config.loc[config[par_name] == 'version', input_type].values[0]
        inputs['file_path'] = "DEPRECATED"

        # Parse start timestamp and categorize days
        inputs['start_timestamp'] = config.loc[config[par_name] == 'DateStart', input_type].values[0]
        dates = pd.date_range(inputs['start_timestamp'], periods=7, freq='D')
        inputs['day_groups'] = pd.DataFrame(
            data={
                "day_group": process_dates_to_groups(dates),
                "date": dates
            },
            index=[f"D{i:02}" for i in range(1, 8)],
        )

        # Hourly values
        inputs['time_horizon'] = [f'H{i:02}' for i in range(1, 169)]
        inputs['daily_horizon'] = [f'H{i:02}' for i in range(1, 8)]
        inputs['rough_zones'] = [f'H{i:02}' for i in range(1, 8)]

        logger.warning("Holidays are not implemented in this version.")

        # Define list of plants
        plant_keys = ['plants', 'gauges', 'nodes', 'river_topology', 'plant_to_node', 'sinks', 'sources']
        initialize_inputs(plant_keys, config, par_name, inputs['time_horizon'], inputs, [])

        # Create incidence matrix for Plants and Gauges
        inputs['river_nodes'] = np.concatenate((inputs['plants'], inputs['gauges']))

        # Process constraint related inputs
        constraint_keys = [
            'sim_folder', 'plt_show',
            'cnstr_bp_ramp', 'cnstr_tur_ramp', 'cnstr_tot_ramp', 'cnstr_gg_ramp',
            'cnstr_temp_t01t24', 'cnstr_bp_t01t24', 'cnstr_tur_t01t24',
            'cnstr_tot_t01t24', 'cnstr_gg_t01t24',
            'cnstr_oper_range', 'sim_type', 'sim_time', 'opt_gap',
            'xy_method', 'edge_elements', 'C_slack',
            'cnstr_pattern_repeat', 'cnstr_rough_zone'
        ]

        # Loop through each key and extract the corresponding value
        for key in constraint_keys:
            inputs[key] = config.loc[config[par_name] == key, input_type].values[0]

        ##################################
        # Process plant related input data
        ##################################
        plant_input_keys = ['Q_tot_daily']
        if inputs['version'] == 'v0.1.2':
            initialize_inputs_with_index(plant_input_keys, config, par_name,
                                         ['Name', input_type], inputs, 'river_nodes', 0)
        else:
            initialize_inputs_with_index(plant_input_keys, config, par_name,
                                         ['Name']+inputs['daily_horizon'], inputs, 'river_nodes', 0)

        plant_input_keys_with_conversion = {
            'Q_max_daily_change': CFS_TO_AFH,
            'WaterToPowerConversion': 1 / CFS_TO_AFH,
        }
        initialize_inputs_with_conversion(plant_input_keys_with_conversion, config, par_name,
                                          ['Name']+inputs['daily_horizon'], inputs, 'river_nodes')

        plant_keys_with_conversion = {
            'Q_bp_ramp_down_max': CFS_TO_AFH,
            'Q_bp_ramp_up_max': CFS_TO_AFH,
            'Q_tur_ramp_down_max': CFS_TO_AFH,
            'Q_tur_ramp_up_max': CFS_TO_AFH,
            'Q_tot_ramp_up_max': CFS_TO_AFH,
            'Q_tot_ramp_down_max': CFS_TO_AFH,
            'Q_gg_ramp_up_max': CFS_TO_AFH,
            'Q_gg_ramp_down_max': CFS_TO_AFH,
            'bp_ramp_down_cyc': 1,
            'bp_ramp_up_cyc': 1,
            'bp_ramp_tot_cyc': 1,
        }
        initialize_inputs_with_conversion(plant_keys_with_conversion, config, par_name,
                                          ['Name', input_type], inputs, 'river_nodes')

        # Hourly values
        plant_hourly_keys = {
            'Q_bp_min_values': CFS_TO_AFH,
            'Q_bp_max_values': CFS_TO_AFH,
            'Q_tur_min_values': CFS_TO_AFH,
            'Q_tur_max_values': CFS_TO_AFH,
            'Q_tot_min_values': CFS_TO_AFH,
            'Q_tot_max_values': CFS_TO_AFH,
            'Q_gg_min_values': CFS_TO_AFH,
            'Q_gg_max_values': CFS_TO_AFH,
            'T_bp_values': 1,
            'T_tur_values': 1,
            'P_tur_min_values': 1,
            'P_tur_max_values': 1,
            'bp_forced_commit': 1,
        }
        initialize_inputs_with_conversion(plant_hourly_keys, config, par_name,
                                          ['Name']+inputs['time_horizon'], inputs, 'river_nodes')

        river_connection_hourly_keys = {
            'Flow_i_j_max': CFS_TO_AFH,
            'Flow_i_j_min': CFS_TO_AFH,
            'T_source_hourly_max_values': 1,
            'T_source_hourly_min_values': 1,
            'T_sink_hourly_max_values': 1,
            'T_sink_hourly_min_values': 1,
        }
        initialize_inputs_with_conversion(river_connection_hourly_keys, config, par_name,
                                          ['Name']+inputs['time_horizon'], inputs, 'river_topology')

        ##################################
        # Process gauge related input data
        ##################################
        gauge_daily_keys = ['T_gauge_daily']
        initialize_inputs_with_index(gauge_daily_keys, config, par_name,
                                     ['Name']+inputs['daily_horizon'], inputs, 'river_nodes', 0)

        gauge_keys = [
            'T_ramp_up_delta',
            'T_ramp_down_delta'
        ]
        initialize_inputs_with_index(gauge_keys, config, par_name,
                                     ['Name', input_type], inputs, 'river_nodes', 0)

        gauge_hourly_min_keys = [
            'T_gauge_hourly_min_values'
        ]
        initialize_inputs_with_index(gauge_hourly_min_keys, config, par_name,
                                     ['Name']+inputs['time_horizon'], inputs, 'gauges', 0)

        gauge_hourly_max_keys = [
            'T_gauge_hourly_max_values'
        ]
        initialize_inputs_with_index(gauge_hourly_max_keys, config, par_name,
                                     ['Name'] + inputs['time_horizon'], inputs, 'gauges', 25)

        inputs['T_gauge_hourly_min_values'] = inputs['T_gauge_hourly_min_values'].reindex(
            inputs['river_nodes'], fill_value=0)
        inputs['T_gauge_hourly_max_values'] = inputs['T_gauge_hourly_max_values'].reindex(
            inputs['river_nodes'], fill_value=25)

        #################################
        # Process node related input data
        #################################
        node_keys = []
        initialize_inputs_with_index(node_keys, config, par_name,
                                     ['Name', input_type], inputs, 'nodes', 0)

        node_hourly_keys = [
            'LMP_values',
            'Demand_values'
        ]
        initialize_inputs_with_index(node_hourly_keys, config, par_name,
                                     ['Name'] + inputs['time_horizon'], inputs, 'nodes', 0)

        ###########################################
        # Process plant to gauge related input data
        ###########################################
        plant_to_gauge_keys = [
            # 'dT_daily'
        ]
        initialize_inputs_with_index(plant_to_gauge_keys, config, par_name,
                                     ['Name', input_type], inputs, 'river_topology', 0)

        plant_to_gauge_daily_keys = [
            'dT_daily'
        ]
        initialize_inputs_with_index(plant_to_gauge_daily_keys, config, par_name,
                                     ['Name']+inputs['daily_horizon'], inputs, 'river_topology', 0)

        plant_to_gauge__hourly_keys = [
            'dT_hourly_values'
        ]
        initialize_inputs_with_index(plant_to_gauge__hourly_keys, config, par_name,
                                     ['Name']+inputs['time_horizon'], inputs, 'river_topology', 0)

        plant_rough_zone_keys = {
            'Q_rough_zone_min': CFS_TO_AFH,
            'Q_rough_zone_max': CFS_TO_AFH
        }
        initialize_inputs_with_conversion(plant_rough_zone_keys, config, par_name,
                                          ['Name']+inputs['rough_zones'], inputs, 'plants', np.nan)

        inputs['Q_rough_zone_min'], inputs['Q_rough_zone_max'], inputs['rough_zones'] = \
            create_rough_zones(inputs['Q_rough_zone_min'], inputs['Q_rough_zone_max'])

        ##########################################
        # Process plant to node related input data
        ##########################################
        plant_to_node_keys = []
        initialize_inputs_with_index(plant_to_node_keys, config, par_name,
                                     ['Name', input_type], inputs, 'plant_to_node', 0)

        ###################
        # Process cost data
        ###################
        # Hourly values
        cost_keys = {
            'C_bp_ramp_up': 1 / CFS_TO_AFH,
            'C_bp_ramp_down': 1 / CFS_TO_AFH,
            'C_tur_ramp_up': 1 / CFS_TO_AFH,
            'C_tur_ramp_down': 1 / CFS_TO_AFH,
            'C_tot_ramp_up': 1 / CFS_TO_AFH,
            'C_tot_ramp_down': 1 / CFS_TO_AFH,
            'C_gg_ramp_up': 1 / CFS_TO_AFH,
            'C_gg_ramp_down': 1 / CFS_TO_AFH,
        }
        initialize_inputs_with_conversion(cost_keys, config, par_name,
                                          ['Name', input_type], inputs, 'river_nodes')

        # Create a DataFrame for the incidence matrix
        inputs['river_incidence_matrix'] = pd.DataFrame(0, index=inputs['river_nodes'],
                                                        columns=inputs['river_topology'])
        inputs['river_adjecency_matrix'] = pd.DataFrame(0, index=inputs['river_nodes'],
                                                        columns=inputs['river_topology'])
        inputs['plants_nodes'] = pd.DataFrame(0, index=inputs['river_nodes'],
                                              columns=inputs['nodes'])

        for connection in inputs['plant_to_node']:
            plant, node = connection.split(' - ')
            inputs['plants_nodes'].loc[plant, node] = 1

        inputs['C_source'] = pd.DataFrame(10000, index=inputs['river_nodes'],
                                          columns=['Single input'])
        inputs['C_source'].loc[inputs['sources']] = 0

        inputs['Q_source_max'] = pd.DataFrame(0, index=inputs['river_nodes'],
                                              columns=['Single input'])
        inputs['Q_source_max'].loc[inputs['sources']] = 10000

        inputs['C_sink'] = pd.DataFrame(10000, index=inputs['river_nodes'],
                                        columns=['Single input'])
        inputs['C_sink'].loc[inputs['sinks']] = 0

        inputs['Q_sink_max'] = pd.DataFrame(0, index=inputs['river_nodes'],
                                            columns=['Single input'])
        inputs['Q_sink_max'].loc[inputs['sinks']] = 10000

        keys = ['Q_tot_daily', 'Q_max_daily_change', 'WaterToPowerConversion',
                'T_gauge_daily', 'dT_daily']
        for key in keys:
            inputs[key].columns = [
                col.replace('H', 'D') if col.startswith('H') else col
                for col in inputs[key].columns
            ]

        inputs['daily_horizon'] = [f'D{i:02}' for i in range(1, 8)]

        return inputs

    except Exception as e:
        logger.error(f'Not able to parse Inputs. Error: {e}')
        sys.exit(1)
