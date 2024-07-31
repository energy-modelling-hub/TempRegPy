from .functions import *
from .plotting import *
from .utils import *
from ortools.math_opt.python import mathopt



def build_and_run(inputs, milp=False):

    # Sets
    plants = ["PlantA"]

    logger.info('Assigning parameters for optimization:')
    parameters = {}
    parameters['LMP'] = {(n, t): value for n, row in inputs['LMP_values'].iterrows() for t, value in row.items()}
    parameters['T_gauge_hourly_max'] = {(g, t): value for g, row in inputs['T_gauge_hourly_max_values'].iterrows() for t, value in row.items()}
    parameters['T_gauge_hourly_min'] = {(g, t): value for g, row in inputs['T_gauge_hourly_min_values'].iterrows() for t, value in row.items()}
    parameters['dT_hourly'] = {(pg, t): value for pg, row in inputs['dT_hourly_values'].iterrows() for t, value in row.items()}
    parameters['T_gauge_daily'] = {(g, s): value for g, row in inputs['T_gauge_daily'].iterrows() for s, value in row.items()}
    parameters['dT_daily'] = {(g, s): value for g, row in inputs['dT_daily'].iterrows() for s, value in row.items()}
    parameters['T_bp'] = {(p, t): value for p, row in inputs['T_bp_values'].iterrows() for t, value in row.items()}
    parameters['T_tur'] = {(p, t): value for p, row in inputs['T_tur_values'].iterrows() for t, value in row.items()}
    parameters['Q_bp_min'] = {(p, t): value for p, row in inputs['Q_bp_min_values'].iterrows() for t, value in row.items()}
    parameters['Q_bp_max'] = {(p, t): value for p, row in inputs['Q_bp_max_values'].iterrows() for t, value in row.items()}
    parameters['Q_tur_min'] = {(p, t): value for p, row in inputs['Q_tur_min_values'].iterrows() for t, value in row.items()}
    parameters['Q_tur_max'] = {(p, t): value for p, row in inputs['Q_tur_max_values'].iterrows() for t, value in row.items()}
    parameters['Q_tot_min'] = {(p, t): value for p, row in inputs['Q_tot_min_values'].iterrows() for t, value in row.items()}
    parameters['Q_tot_max'] = {(p, t): value for p, row in inputs['Q_tot_max_values'].iterrows() for t, value in row.items()}
    parameters['Q_gg_min'] = {(p, t): value for p, row in inputs['Q_gg_min_values'].iterrows() for t, value in row.items()}
    parameters['Q_gg_max'] = {(p, t): value for p, row in inputs['Q_gg_max_values'].iterrows() for t, value in row.items()}
    parameters['Q_source_max'] = {(p, t): value for p, row in inputs['Q_source_max'].iterrows() for t, value in row.items()}
    parameters['Q_sink_max'] = {(p, t): value for p, row in inputs['Q_sink_max'].iterrows() for t, value in row.items()}
    parameters['P_tur_min'] = {(p, t): value for p, row in inputs['P_tur_min_values'].iterrows() for t, value in row.items()}
    parameters['P_tur_max'] = {(p, t): value for p, row in inputs['P_tur_max_values'].iterrows() for t, value in row.items()}
    parameters['Demand'] = {(n, t): value for n, row in inputs['Demand_values'].iterrows() for t, value in row.items()}
    parameters['Q_bp_ramp_up_max'] = {(p, t): value for p, row in inputs['Q_bp_ramp_up_max'].iterrows() for t, value in row.items()}
    parameters['Q_bp_ramp_down_max'] = {(p, t): value for p, row in inputs['Q_bp_ramp_down_max'].iterrows() for t, value in row.items()}
    parameters['Q_tur_ramp_up_max'] = {(p, t): value for p, row in inputs['Q_tur_ramp_up_max'].iterrows() for t, value in row.items()}
    parameters['Q_tur_ramp_down_max'] = {(p, t): value for p, row in inputs['Q_tur_ramp_down_max'].iterrows() for t, value in row.items()}
    parameters['Q_tot_ramp_up_max'] = {(p, t): value for p, row in inputs['Q_tot_ramp_up_max'].iterrows() for t, value in row.items()}
    parameters['Q_tot_ramp_down_max'] = {(p, t): value for p, row in inputs['Q_tot_ramp_down_max'].iterrows() for t, value in row.items()}
    parameters['Q_gg_ramp_up_max'] = {(p, t): value for p, row in inputs['Q_gg_ramp_up_max'].iterrows() for t, value in row.items()}
    parameters['Q_gg_ramp_down_max'] = {(p, t): value for p, row in inputs['Q_gg_ramp_down_max'].iterrows() for t, value in row.items()}
    parameters['River_incidence_matrix'] = {(rn, rl): value for rn, row in inputs['river_incidence_matrix'].iterrows() for rl, value in row.items()}
    parameters['River_adjecency_matrix'] = {(p, rn): value for p, row in inputs['river_adjecency_matrix'].iterrows() for rn, value in row.items()}
    parameters['Flow_i_j_max'] = {
        (i, j, t): inputs['Flow_i_j_max'].loc[f'{i} - {j}', t] if f'{i} - {j}' in inputs['Flow_i_j_max'].index else 0
        for i in inputs['river_nodes'] for j in inputs['river_nodes'] for t in inputs['time_horizon']
    }
    parameters['Flow_i_j_min'] = {
        (i, j, t): (
            inputs['Flow_i_j_min'].loc[f'{i} - {j}', t] if not inputs['Flow_i_j_min'].empty and f'{i} - {j}' in inputs[
                'Flow_i_j_min'].index else 0)
        for i in inputs['river_nodes'] for j in inputs['river_nodes'] for t in inputs['time_horizon']
    }
    parameters['Plants_to_nodes'] = {(p, n): value for p, row in inputs['plants_nodes'].iterrows() for n, value in row.items()}
    parameters['C_bp_ramp_up'] = {(p, s): value for p, row in inputs['C_bp_ramp_up'].iterrows() for s, value in row.items()}
    parameters['C_bp_ramp_down'] = {(p, s): value for p, row in inputs['C_bp_ramp_down'].iterrows() for s, value in row.items()}
    parameters['C_tur_ramp_up'] = {(p, s): value for p, row in inputs['C_tur_ramp_up'].iterrows() for s, value in row.items()}
    parameters['C_tur_ramp_down'] = {(p, s): value for p, row in inputs['C_tur_ramp_down'].iterrows() for s, value in row.items()}
    parameters['C_tot_ramp_up'] = {(p, s): value for p, row in inputs['C_tot_ramp_up'].iterrows() for s, value in row.items()}
    parameters['C_tot_ramp_down'] = {(p, s): value for p, row in inputs['C_tot_ramp_down'].iterrows() for s, value in row.items()}
    parameters['C_gg_ramp_up'] = {(p, s): value for p, row in inputs['C_gg_ramp_up'].iterrows() for s, value in row.items()}
    parameters['C_gg_ramp_down'] = {(p, s): value for p, row in inputs['C_gg_ramp_down'].iterrows() for s, value in row.items()}
    parameters['C_source'] = {(p, s): value for p, row in inputs['C_source'].iterrows() for s, value in row.items()}
    parameters['C_sink'] = {(p, s): value for p, row in inputs['C_sink'].iterrows() for s, value in row.items()}
    parameters['Q_tot_daily'] = {(p, s): value for p, row in inputs['Q_tot_daily'].iterrows() for s, value in row.items()}
    parameters['Q_max_daily_change'] = {(p, s): value for p, row in inputs['Q_max_daily_change'].iterrows() for s, value in row.items()}
    parameters['WaterToPowerConversion'] = {(p, s): value for p, row in inputs['WaterToPowerConversion'].iterrows() for s, value in row.items()}


    def log_sample_summary(logger, name, parameter_dict, sample_size=5):
        logger.debug(f"{name} assigned (sample): {list(parameter_dict.values())[:sample_size]} ... (total: {len(parameter_dict)})")

    # Log summary of node values
    log_sample_summary(logger, "LMP values", parameters['LMP'])
    log_sample_summary(logger, "Demand values", parameters['Demand'])

    # Log summary of temperature and demand parameters
    log_sample_summary(logger, "T_gauge_hourly_max values", parameters['T_gauge_hourly_max'])
    log_sample_summary(logger, "T_gauge_hourly_min values", parameters['T_gauge_hourly_min'])
    log_sample_summary(logger, "dT_hourly values", parameters['dT_hourly'])

    # Log total counts for other parameters
    log_sample_summary(logger, "T_bp", parameters['T_bp'])
    log_sample_summary(logger, "T_tur", parameters['T_tur'])
    log_sample_summary(logger, "Q_bp_min", parameters['Q_bp_min'])
    log_sample_summary(logger, "Q_bp_max", parameters['Q_bp_max'])
    log_sample_summary(logger, "Q_tur_min", parameters['Q_tur_min'])
    log_sample_summary(logger, "Q_tur_max", parameters['Q_tur_max'])
    log_sample_summary(logger, "Q_tot_min", parameters['Q_tot_min'])
    log_sample_summary(logger, "Q_tot_max", parameters['Q_tot_max'])
    log_sample_summary(logger, "Q_gg_min", parameters['Q_gg_min'])
    log_sample_summary(logger, "Q_gg_max", parameters['Q_gg_max'])
    log_sample_summary(logger, "P_tur_min", parameters['P_tur_min'])
    log_sample_summary(logger, "P_tur_max", parameters['P_tur_max'])
    log_sample_summary(logger, 'Q_bp_ramp_up_max', parameters['Q_bp_ramp_up_max'])
    log_sample_summary(logger, 'Q_bp_ramp_down_max', parameters['Q_bp_ramp_down_max'])
    log_sample_summary(logger, 'Q_tur_ramp_up_max', parameters['Q_tur_ramp_up_max'])
    log_sample_summary(logger, 'Q_tur_ramp_down_max', parameters['Q_tur_ramp_down_max'])
    log_sample_summary(logger, 'Q_tot_ramp_up_max', parameters['Q_tot_ramp_up_max'])
    log_sample_summary(logger, 'Q_tot_ramp_down_max', parameters['Q_tot_ramp_down_max'])
    log_sample_summary(logger, 'Q_gg_ramp_up_max', parameters['Q_gg_ramp_up_max'])
    log_sample_summary(logger, 'Q_gg_ramp_down_max', parameters['Q_gg_ramp_down_max'])
    log_sample_summary(logger, 'C_bp_ramp_up', parameters['C_bp_ramp_up'])
    log_sample_summary(logger, 'C_bp_ramp_down', parameters['C_bp_ramp_down'])
    log_sample_summary(logger, 'C_tur_ramp_up', parameters['C_tur_ramp_up'])
    log_sample_summary(logger, 'C_tur_ramp_down', parameters['C_tur_ramp_down'])
    log_sample_summary(logger, 'C_tot_ramp_up', parameters['C_tot_ramp_up'])
    log_sample_summary(logger, 'C_tot_ramp_down', parameters['C_tot_ramp_down'])
    log_sample_summary(logger, 'C_gg_ramp_up', parameters['C_gg_ramp_up'])
    log_sample_summary(logger, 'C_gg_ramp_down', parameters['C_gg_ramp_down'])
    log_sample_summary(logger, 'C_source', parameters['C_source'])
    log_sample_summary(logger, 'C_sink', parameters['C_sink'])
    log_sample_summary(logger, 'Q_tot_daily', parameters['Q_tot_daily'])
    log_sample_summary(logger, 'Q_max_daily_change', parameters['Q_max_daily_change'])
    log_sample_summary(logger, 'WaterToPowerConversion', parameters['WaterToPowerConversion'])

    model = mathopt.Model(name="By-Pass Optimization")

    # Decision variables
    variables = {}
    # Variables
    variables['q_tot_min'] = [model.add_variable(lb=min(value for (p, t), value in parameters['Q_tot_min'].items() if p == plant),
                                                 ub=max(value for (p, t), value in parameters['Q_tot_max'].items() if p == plant),
                                                 name=f'q_tot_min_{plant}') for plant in inputs['river_nodes']
                              ]
    variables['q_bp'] = [[model.add_variable(lb=parameters['Q_bp_min'][p, t],
                                             ub=parameters['Q_bp_max'][p, t],
                                             name=f'q_bp_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_tur'] = [[model.add_variable(lb=parameters['Q_tur_min'][p, t],
                                              ub=parameters['Q_tur_max'][p, t],
                                              name=f'q_tur_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_tot'] = [[model.add_variable(lb=parameters['Q_tot_min'][p, t],
                                              ub=parameters['Q_tot_max'][p, t],
                                              name=f'q_tot_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_gg'] = [[model.add_variable(lb=parameters['Q_gg_min'][p, t],
                                             ub=parameters['Q_gg_max'][p, t],
                                             name=f'q_gg_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                        ]
    variables['q_source'] = [[model.add_variable(lb=0,
                                                 ub=parameters['Q_source_max'][p, 'Single input'],
                                                 name=f'q_source_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                            ]
    variables['q_sink'] = [[model.add_variable(lb=0,
                                               ub=parameters['Q_sink_max'][p, 'Single input'],
                                               name=f'q_sink_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                          ]
    # variables['q_flow'] = [[model.add_variable(lb=0,
    #                                            ub=100000,
    #                                            name=f'q_flow_{rn}_{t}') for t in inputs['time_horizon']] for rn in inputs['river_topology']
    #                     ]
    variables['q_flow'] = [[[model.add_variable(lb=parameters['Flow_i_j_min'][i,j,t],
                                                ub=parameters['Flow_i_j_max'][i,j,t],
                                                name=f'q_flow_{i}_{j}_{t}') for t in inputs['time_horizon']] for i in inputs['river_nodes']] for j in inputs['river_nodes']
                          ]
    variables['q_in_flow'] = [[model.add_variable(lb=0,
                                                  ub=100000,
                                                  name=f'q_in_flow_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                             ]
    variables['q_out_flow'] = [[model.add_variable(lb=0,
                                                   ub=100000,
                                                   name=f'q_out_flow_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                              ]
    variables['q_bp_ramp_up'] = [[model.add_variable(lb=0,
                                                     ub=parameters['Q_bp_ramp_up_max'][p, 'Single input'],
                                                     name=f'q_bp_ramp_up_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_bp_ramp_down'] = [[model.add_variable(lb=0,
                                                       ub=parameters['Q_bp_ramp_down_max'][p, 'Single input'],
                                                       name=f'q_bp_ramp_down_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_tur_ramp_up'] = [[model.add_variable(lb=0,
                                                      ub=parameters['Q_tur_ramp_up_max'][p, 'Single input'],
                                                      name=f'q_tur_ramp_up_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_tur_ramp_down'] = [[model.add_variable(lb=0,
                                                        ub=parameters['Q_tur_ramp_down_max'][p, 'Single input'],
                                                        name=f'q_tur_ramp_down_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_tot_ramp_up'] = [[model.add_variable(lb=0,
                                                      ub=parameters['Q_tot_ramp_up_max'][p, 'Single input'],
                                                      name=f'q_tot_ramp_up_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_tot_ramp_down'] = [[model.add_variable(lb=0,
                                                        ub=parameters['Q_tot_ramp_down_max'][p, 'Single input'],
                                                        name=f'q_tot_ramp_down_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_gg_ramp_up'] = [[model.add_variable(lb=0,
                                                     ub=parameters['Q_gg_ramp_up_max'][p, 'Single input'],
                                                     name=f'q_gg_ramp_up_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['q_gg_ramp_down'] = [[model.add_variable(lb=0,
                                                       ub=parameters['Q_gg_ramp_down_max'][p, 'Single input'],
                                                       name=f'q_gg_ramp_down_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    variables['p_tur'] = [[model.add_variable(lb=parameters['P_tur_min'][p, t],
                                              ub=parameters['P_tur_max'][p, t],
                                              name=f'p_tur_{p}_{t}') for t in inputs['time_horizon']] for p in inputs['river_nodes']
                         ]
    logger.info(f"Optimization variables sucesfully created. {list(variables)}")

    # Objective
    # obj_fnc = mathopt.LinearExpression()
    # # Add constraints for total hourly release
    # for p in range(len(inputs['river_nodes'])):
    #     plant = inputs['river_nodes'][p]
    #     for t in range(len(inputs['time_horizon'])):
    #         time = inputs['time_horizon'][t]
    #         for n in range(len(inputs['nodes'])):
    #             node = inputs['nodes'][n]
    #             obj_fnc += (variables['p_tur'][p][t] * parameters['LMP'][node,time] * parameters['plants_nodes'][plant,node]
    #                         - variables['q_bp_ramp_up'][p][t] * parameters['C_bp_ramp_up'][plant, 'Single input']
    #                         - variables['q_bp_ramp_down'][p][t] * parameters['C_bp_ramp_down'][plant, 'Single input']
    #                         - variables['q_tur_ramp_up'][p][t] * parameters['C_tur_ramp_up'][plant, 'Single input']
    #                         - variables['q_tur_ramp_down'][p][t] * parameters['C_tur_ramp_down'][plant, 'Single input']
    #                         - variables['q_tot_ramp_up'][p][t] * parameters['C_tot_ramp_up'][plant, 'Single input']
    #                         - variables['q_tot_ramp_down'][p][t] * parameters['C_tot_ramp_down'][plant, 'Single input'])
    obj_fnc = mathopt.LinearExpression()
    # Add constraints for total hourly release
    for p in range(len(inputs['river_nodes'])):
        plant = inputs['river_nodes'][p]
        for t in range(len(inputs['time_horizon'])):
            time = inputs['time_horizon'][t]
            obj_fnc += (sum(variables['p_tur'][p][t] * parameters['LMP'][n, time] * parameters['Plants_to_nodes'][plant, n] for n in inputs['nodes'])
                        - variables['q_bp_ramp_up'][p][t] * parameters['C_bp_ramp_up'][plant, 'Single input']
                        - variables['q_bp_ramp_down'][p][t] * parameters['C_bp_ramp_down'][plant, 'Single input']
                        - variables['q_tur_ramp_up'][p][t] * parameters['C_tur_ramp_up'][plant, 'Single input']
                        - variables['q_tur_ramp_down'][p][t] * parameters['C_tur_ramp_down'][plant, 'Single input']
                        - variables['q_tot_ramp_up'][p][t] * parameters['C_tot_ramp_up'][plant, 'Single input']
                        - variables['q_tot_ramp_down'][p][t] * parameters['C_tot_ramp_down'][plant, 'Single input']
                        - variables['q_gg_ramp_up'][p][t] * parameters['C_gg_ramp_up'][plant, 'Single input']
                        - variables['q_gg_ramp_down'][p][t] * parameters['C_gg_ramp_down'][plant, 'Single input']
                        - variables['q_source'][p][t] * parameters['C_source'][plant, 'Single input']
                        - variables['q_sink'][p][t] * parameters['C_sink'][plant, 'Single input'])

    model.maximize(obj_fnc)

    # Constraints
    constraints = []
    constraint_id_main = []
    constraint_id_unit = []
    constraint_id_time = []

    ###################################
    ######## TOTAL RELEASE
    ###################################
    # Add constraints for total hourly release
    for p in range(len(inputs['river_nodes'])):
        for t in range(len(inputs['time_horizon'])):
            constraint_id_main.append('Total hourly release')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append(f'{inputs['time_horizon'][t]}')
            constraints.append(model.add_linear_constraint(variables['q_bp'][p][t] + variables['q_tur'][p][t] == variables['q_tot'][p][t]))

    # Add constraint for total daily release
    for p in range(len(inputs['river_nodes'])):
        constraint_id_main.append('Total daily release')
        constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
        constraint_id_time.append('')
        constraints.append(model.add_linear_constraint(sum(variables['q_tot'][p][t] for t in range(len(inputs['time_horizon']))) == parameters['Q_tot_daily'][inputs['river_nodes'][p],'Single input']))

    # Add constraint for outflows from a node p
    for i in range(len(inputs['river_nodes'])):
        for t in range(len(inputs['time_horizon'])):
            constraint_id_main.append('Outgoing flows')
            constraint_id_unit.append(f'{inputs['river_nodes'][i]}')
            constraint_id_time.append(f'{inputs['time_horizon'][t]}')
            constraints.append(model.add_linear_constraint(variables['q_out_flow'][i][t] == sum(variables['q_flow'][i][j][t] for j in range(len(inputs['river_nodes'])))))

    # Add a constraint for inflows into a node p
    for i in range(len(inputs['river_nodes'])):
        for t in range(len(inputs['time_horizon'])):
            constraint_id_main.append('Incoming flows')
            constraint_id_unit.append(f'{inputs['river_nodes'][i]}')
            constraint_id_time.append(f'{inputs['time_horizon'][t]}')
            constraints.append(model.add_linear_constraint(variables['q_in_flow'][i][t] == sum(variables['q_flow'][j][i][t] for j in range(len(inputs['river_nodes'])))))


    # Add constraints for hourly flows between nodes
    for p in range(len(inputs['river_nodes'])):
        for t in range(len(inputs['time_horizon'])):
            constraint_id_main.append('Total hourly inflows')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append(f'{inputs['time_horizon'][t]}')
            # constraints.append(model.add_linear_constraint(variables['q_sink'][p][t] + variables['q_gg'][p][t] + variables['q_bp'][p][t] + variables['q_tur'][p][t] == variables['q_source'][p][t] + sum(parameters['River_topology_matrix'][inputs['river_topology'][rn],inputs['river_nodes'][p]]*variables['q_flow'][rn][t] for rn in range(len(inputs['river_topology'])))))
            constraints.append(model.add_linear_constraint(variables['q_gg'][p][t] + variables['q_bp'][p][t] + variables['q_tur'][p][t] ==
                                                           variables['q_sink'][p][t] + variables['q_in_flow'][p][t]))

    # Add constraints for hourly flows between nodes
    for p in range(len(inputs['river_nodes'])):
        for t in range(len(inputs['time_horizon'])):
            constraint_id_main.append('Total hourly inflows')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append(f'{inputs['time_horizon'][t]}')
            constraints.append(model.add_linear_constraint(variables['q_gg'][p][t] + variables['q_bp'][p][t] + variables['q_tur'][p][t] ==
                                                           variables['q_source'][p][t] + variables['q_out_flow'][p][t]))

    ###################################
    ######## CYCLIC CONDITIONS
    ###################################
    # Add constraint for bypass cyclic condition
    if inputs['cnstr_bp_t01t24']:
        logger.info('Bypass release cyclic constraints (H01=H24) have been included in the optimization.')
        if inputs['cnstr_temp_t01t24']:
            logger.warning('Bypass release cyclic constraints (H01=H24) may conflict with cyclic temperature constraints.')
        for p in range(len(inputs['river_nodes'])):
            constraint_id_main.append('q_bp t01 = t24')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append('')
            constraints.append(model.add_linear_constraint(variables['q_bp'][p][0] == variables['q_bp'][p][len(inputs['time_horizon'])-1]))

    # Add constraint for turbine cyclic condition
    if inputs['cnstr_tur_t01t24']:
        logger.info('Turbine release cyclic constraints (H01=H24) have been included in the optimization.')
        if inputs['cnstr_temp_t01t24']:
            logger.warning('Turbine release cyclic constraints (H01=H24) may conflict with cyclic temperature constraints.')
        for p in range(len(inputs['river_nodes'])):
            constraint_id_main.append('q_tur t01 = t24')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append('')
            constraints.append(model.add_linear_constraint(
                variables['q_tur'][p][0] == variables['q_tur'][p][len(inputs['time_horizon']) - 1]))

    # Add constraint for total release cyclic condition
    if inputs['cnstr_tot_t01t24']:
        logger.info('Total release cyclic constraints (H01=H24) have been included in the optimization.')
        if inputs['cnstr_temp_t01t24']:
            logger.warning('Total release cyclic constraints (H01=H24) may conflict with cyclic temperature constraints.')
        for p in range(len(inputs['river_nodes'])):
            constraint_id_main.append('q_tot t01 = t24')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append('')
            constraints.append(model.add_linear_constraint(
                variables['q_tot'][p][0] == variables['q_tot'][p][len(inputs['time_horizon']) - 1]))

    # Add constraint for gauge cyclic condition
    if inputs['cnstr_gg_t01t24']:
        logger.info('Gauge release cyclic constraints (H01=H24) have been included in the optimization.')
        if inputs['cnstr_temp_t01t24']:
            logger.warning('Gauge release cyclic constraints (H01=H24) may conflict with cyclic temperature constraints.')
        for p in range(len(inputs['river_nodes'])):
            constraint_id_main.append('q_gg t01 = t24')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append('')
            constraints.append(model.add_linear_constraint(
                variables['q_gg'][p][0] == variables['q_gg'][p][len(inputs['time_horizon']) - 1]))

    ###################################
    ######## OPERATING RANGE
    ###################################
    # Add constraint for maximum daily operating range
    if inputs['cnstr_oper_range'] is True:
        logger.info('Maximum daily operating range constraints have been included in the optimization.')
        # Add constraints for maximum total daily ramping rate 8000CFS
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                constraint_id_main.append('Maximum daily operating range - min')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_tot_min'][p] <= variables['q_tot'][p][t]))
        # Add constraints for maximum total daily ramping rate 8000CFS
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                constraint_id_main.append('Maximum daily operating range - max')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_tot_min'][p] + parameters['Q_max_daily_change'][inputs['river_nodes'][p],'Single input'] >= variables['q_tot'][p][t]))

    ###################################
    ######## RAMPING RATES
    ###################################
    # Add constraint for bypass ramping rates
    if inputs['cnstr_bp_ramp'] is True:
        logger.info('Bypass release ramping constraints have been included in the optimization.')
        # Add constraint for bypass ramping up rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp up constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Bypass ramping up')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_bp'][p][t] - variables['q_bp'][p][prev_t] <= variables['q_bp_ramp_up'][p][t]))

        # Add constraint for bypass ramping down rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp down constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Bypass ramping down')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_bp'][p][prev_t] - variables['q_bp'][p][t] <= variables['q_bp_ramp_down'][p][t]))

    # Add constraint for turbine ramping rates
    if inputs['cnstr_tur_ramp'] is True:
        logger.info('Turbine release ramping constraints have been included in the optimization.')
        # Add constraint for turbine ramping up rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp up constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Turbine ramping up')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_tur'][p][t] - variables['q_tur'][p][prev_t] <= variables['q_tur_ramp_up'][p][t]))

        # Add constraint for turbine ramping down rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp down constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Turbine ramping down')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_tur'][p][prev_t] - variables['q_tur'][p][t] <= variables['q_tur_ramp_down'][p][t]))

    # Add constraint for total ramping rates
    if inputs['cnstr_tot_ramp'] is True:
        logger.info('Total release ramping constraints have been included in the optimization.')
        # Add constraint for total ramping up rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp up constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Total ramping up')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_tot'][p][t] - variables['q_tot'][p][prev_t] <= variables['q_tot_ramp_up'][p][t]))

        # Add constraint for total ramping down rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp down constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Total ramping down')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_tot'][p][prev_t] - variables['q_tot'][p][t] <= variables['q_tot_ramp_down'][p][t]))

    # Add constraint for gauge ramping rates
    if inputs['cnstr_gg_ramp'] is True:
        logger.info('Gauge release ramping constraints have been included in the optimization.')
        # Add constraint for gauge ramping up rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp up constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Gauge ramping up')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_gg'][p][t] - variables['q_gg'][p][prev_t] <= variables['q_gg_ramp_up'][p][t]))

        # Add constraint for gauge ramping down rate
        for p in range(len(inputs['river_nodes'])):
            for t in range(len(inputs['time_horizon'])):
                prev_t = t-1 if t > 0 else len(inputs['time_horizon'])-1  # Handling wrap-around
                # Add ramp down constraints
                # If t is the first time period, compare it with the last time period to ensure cyclical ramp constraint
                constraint_id_main.append('Gauge ramping down')
                constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
                constraint_id_time.append(f'{inputs['time_horizon'][t]}')
                constraints.append(model.add_linear_constraint(variables['q_gg'][p][prev_t] - variables['q_gg'][p][t] <= variables['q_gg_ramp_down'][p][t]))
    ###################################
    ######## POWER BALANCE
    ###################################
    # Add constraints for power output
    for p in range(len(inputs['river_nodes'])):
        for t in range(len(inputs['time_horizon'])):
            constraint_id_main.append('Power Output')
            constraint_id_unit.append(f'{inputs['river_nodes'][p]}')
            constraint_id_time.append(f'{inputs['time_horizon'][t]}')
            constraints.append(model.add_linear_constraint(variables['p_tur'][p][t] == variables['q_tur'][p][t] * parameters['WaterToPowerConversion'][inputs['river_nodes'][p],'Single input']))

    # Add constraints for power balance
    for n in range(len(inputs['nodes'])):
        node = inputs['nodes'][n]
        for t in range(len(inputs['time_horizon'])):
            time = inputs['time_horizon'][t]
            constraint_id_main.append('Power Demand Balance')
            constraint_id_unit.append(f'{inputs['nodes'][n]}')
            constraint_id_time.append(f'{inputs['time_horizon'][t]}')
            constraints.append(model.add_linear_constraint(parameters['Demand'][node,time] - sum(variables['p_tur'][p][t] * parameters['Plants_to_nodes'][inputs['river_nodes'][p],node] for p in range(len(inputs['river_nodes']))) >= 0))

    ###################################
    ######## TEMPERATURE
    ###################################


    params = mathopt.SolveParameters(enable_output=True)
    result = mathopt.solve(model, mathopt.SolverType.GLOP, params=params)
    assert result.termination.reason == mathopt.TerminationReason.OPTIMAL
    results = result.variable_values()
    duals = result.dual_values()

    return inputs, results, duals



