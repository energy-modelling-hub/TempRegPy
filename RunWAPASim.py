import os
import logging
import colorlog
import datetime
import pandas as pd
import tempregpy as trp
from ortools.math_opt.python import mathopt
from tempregpy.model import prepare_model, parse_model_results
# from tempregpy.wapa import export_results_to_excel, load_inputs_from_excel
import tempregpy.wapa as wapa

TIMESTAMP = datetime.datetime.now()
RESULTS_DIR = f"./results_{TIMESTAMP.strftime('%Y%m%d_%H%M%S')}/"

# TODO configure logger here...
# TODO use global logger in model run

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

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

WAPA_INPUT_EXCEL_FILE = "./WAPA Inputs.xlsm"

excel_file = pd.ExcelFile(
    os.path.abspath(WAPA_INPUT_EXCEL_FILE)
)
excel_data = excel_file.parse("Inputs")

inputs = wapa.load_inputs_from_excel(excel_data)

logger.info("Preparing model with inputs...")
model, variables, constraints = prepare_model(inputs)

params = mathopt.SolveParameters(enable_output=True, time_limit=datetime.timedelta(seconds=10))
logger.info("Starting MathOpt solver...")
solve_result = mathopt.solve(model, mathopt.SolverType.HIGHS, params=params)

results = parse_model_results(inputs, solve_result, variables)

logger.info("Model solved successfully. Exporting results to Excel...")
wapa.export_results_to_excel(inputs, results, os.path.join(RESULTS_DIR, "WAPA_Results.xlsx"))

logger.info(f"Results saved in {os.path.abspath(RESULTS_DIR)}")