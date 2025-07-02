import os
import logging
import colorlog
import datetime
import pandas as pd
import tempregpy as trp
from ortools.math_opt.python import mathopt
# from tempregpy.model import prepare_model, parse_model_results
import tempregpy.wapa as wapa
from tempregpy.model import Model, ModelConfig, parse_model_results

TIMESTAMP = datetime.datetime.now()
print(TIMESTAMP)
# RESULTS_DIR = f"./results_{TIMESTAMP.strftime('%Y%m%d_%H%M%S')}/"
RESULTS_DIR = f"./Results - {TIMESTAMP.strftime('%b %d, %Y %I.%M.%S %p')}/"

def get_console_handler():
    class SingleLetterFilter(logging.Filter):
        LEVEL_LETTERS = {
            'DEBUG': 'D',
            'INFO': 'I', 
            'WARNING': 'W',
            'ERROR': 'E',
            'CRITICAL': 'C'
        }
        
        def filter(self, record):
            record.levelname_short = self.LEVEL_LETTERS.get(record.levelname, 'U')
            return True
        
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        '%(light_black)s[%(log_color)s%(levelname_short)s%(light_black)s]%(reset)s %(name)s: %(message_log_color)s%(message)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'light_green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={
            'message': {
                'DEBUG': 'light_black',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        },
        style='%'
    )
    handler.setFormatter(formatter)
    handler.addFilter(SingleLetterFilter())
    return handler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        get_console_handler(),
    ],
)

logger = logging.getLogger(__name__)



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
    solver_type=mathopt.SolverType.HIGHS
)

model = Model(config)
logger.info("Preparing model with inputs...")
model.populate_from_inputs(inputs)
solve_result = model.solve()

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


# if inputs['plt_show']:
for unit_name in inputs['plants']:
    plot_data = pd.concat([results['q_bp'].loc[:, unit_name], results['q_tur'].loc[:, unit_name]], axis=1).set_axis(['q_bp', 'q_tur'], axis=1).clip(lower=0)
    plot_data['LMP'] = get_lmp_values_for_plant(unit_name, inputs['plant_to_node'], inputs['LMP_values'])
    trp.plot_dispatch(plot_data[['q_bp','q_tur']], plot_data[['LMP']], save_fig=True, fig_name=RESULTS_DIR + '/plot.png', unit_name=unit_name)
    df_dispatch = inputs['Demand_values'].copy().T
    df_dispatch = pd.concat([df_dispatch, results['p_tur']], axis=1)
    trp.plot_load_serving(df_dispatch,save_fig=True, fig_name=RESULTS_DIR + '/pload_serving.png', unit_name=unit_name, node_name='Node 1')


logger.info("Model solved successfully. Exporting results to Excel...")
wapa.export_results_to_excel(excel_data, inputs, results, os.path.join(RESULTS_DIR, "WAPA_Results.xlsx"))

import glob
png_files = glob.glob(os.path.join(RESULTS_DIR, "*.png"))

# for file_path in png_files:
#     try:
#         os.remove(file_path)
#         print(f"Removed: {file_path}")
#     except OSError as e:
#         print(f"Error removing {file_path}: {e}")

logger.info(f"Results saved in {os.path.abspath(RESULTS_DIR)}")

