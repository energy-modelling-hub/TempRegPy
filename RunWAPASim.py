import os
import sys
import datetime
import pandas as pd
from ortools.math_opt.python import mathopt
import tempregpy.wapa as wapa
from tempregpy.model import *
from tempregpy.wapa.plots import *


TIMESTAMP = datetime.datetime.now()
print(TIMESTAMP)
# RESULTS_DIR = f"./results_{TIMESTAMP.strftime('%Y%m%d_%H%M%S')}/"
RESULTS_DIR = f"./Results - {TIMESTAMP.strftime('%b %d, %Y %I.%M.%S %p')}/"


WAPA_INPUT_EXCEL_FILE = "./WAPA Inputs.xlsm"

excel_file = pd.ExcelFile(
    os.path.abspath(WAPA_INPUT_EXCEL_FILE)
)
excel_data = excel_file.parse("Inputs")

inputs = wapa.load_inputs_from_excel(excel_data)

RESULTS_DIR = inputs["sim_folder"]

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)


config = ModelConfig(
    name="Bypass Optimization",
    solver_type=mathopt.SolverType.HIGHS,
    product_linearization=ProductLinearizationConfig(
        # method=ProductLinearizationMethod.SINGLE,
        # method=ProductLinearizationMethod.TRIANGLES,
        # method=ProductLinearizationMethod.POLYGONS,
        method=ProductLinearizationMethod.SUM_OF_CONVEX,
        N=inputs['edge_elements'],
    )
)

model = Model(config)
logger.info("Preparing model with inputs...")
model.populate_from_inputs(inputs)

try:
    solve_result = model.solve(time_limit=inputs['sim_time'],optimality_gap=inputs['opt_gap'])
except KeyboardInterrupt as e:
    logger.error("Model solving interrupted by user.")
    sys.exit(1)

results = parse_model_results(inputs, solve_result, model.variables)
with open("./output.pkl", "wb") as f:
    import pickle
    pickle.dump((excel_data, inputs, results), f)

def get_lmp_values_for_plant(plant_name, plant_to_node, lmp_values):
    # Generate the plant_node_mapping from plant_to_node
    plant_node_mapping = {entry.split(' - ')[0]: entry.split(' - ')[1] for entry in plant_to_node}

    # Get the node name for the given plant
    node_name = plant_node_mapping.get(plant_name)
    if node_name:
        return lmp_values.loc[node_name]
    else:
        raise ValueError(f"Plant {plant_name} not found in the mapping.")



for unit_name in inputs['plants']:
    plot_data = pd.concat([results['q_bp'].loc[:, unit_name], results['q_tur'].loc[:, unit_name]], axis=1).set_axis(['q_bp', 'q_tur'], axis=1).clip(lower=0)
    plot_data['LMP'] = get_lmp_values_for_plant(unit_name, inputs['plant_to_node'], inputs['LMP_values'])
    fig = plot_dispatch(plot_data[['q_bp','q_tur']], plot_data[['LMP']], unit_name=unit_name)
    fig.savefig(os.path.join(RESULTS_DIR, f"{unit_name}_dispatch.png"), format='png')

    if inputs['plt_show']:
        logger.warning(f"Showing \"Dispatch\" plot for {unit_name}")
        plt.show()

    df_dispatch = inputs['Demand_values'].copy().T
    df_dispatch = pd.concat([df_dispatch, results['p_tur']], axis=1)
    fig = plot_load_serving(df_dispatch, unit_name=unit_name, node_name='Node 1')
    fig.savefig(os.path.join(RESULTS_DIR, f"{unit_name}_load_serving.png"), format='png')

    if inputs['plt_show']:
        logger.warning(f"Showing \"Load Serving\" plot for {unit_name}")
        plt.show()


logger.info("Model solved successfully. Exporting results to Excel...")
wapa.export_results_to_excel(excel_data, inputs, results, os.path.join(RESULTS_DIR, "WAPA_Results.xlsx"))

logger.info(f"Results saved in {os.path.abspath(RESULTS_DIR)}")

