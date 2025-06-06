import xlsxwriter
from xlsxwriter.utility import xl_range
import numpy as np
import pandas as pd
import os

def export_results_to_excel(inputs, results, file_path):
    workbook = xlsxwriter.Workbook(file_path)

    BASE_COLUMNS = [{
        "label": "Hour",
        "unit": "-",
        "internal_key": "hour",
        "data": np.linspace(1, len(results["p_tur"]), len(results["p_tur"])),
    },{
        "label": "Location Marginal Price",
        "unit": "USD/MWh??",
        "internal_key": "lmp",
        "data": inputs["LMP_values"].loc["Node 1"]
    }]
    RESULT_NODES = ["GCD", "RM61"]
    COLUMN_MAP = {}

    for node in RESULT_NODES:
        COLUMN_MAP[node] = BASE_COLUMNS.copy()

        COLUMN_MAP[node].extend([{
            "label": "Turbine Power",
            "unit": "MW",
            "internal_key": "p_tur",
            "data": results["p_tur"].loc[:, node],
        },{
            "label": "Bypass Flow",
            "unit": "CFS",
            "internal_key": "q_bp",
            "data": results["q_bp"].loc[:, node],
        },{
            "label": "Total Plant Release",
            "unit": "CFS",
            "internal_key": "q_tot",
            "data": results["q_tot"].loc[:, node],
        },{
            "label": "Plant Temperature",
            "unit": "°C",
            "internal_key": "T_plant",
            "data": results["T_plant"].loc[:, node],
        },{
            "label": "Bypass Commitment Status",
            "unit": "-",
            "internal_key": "q_bp_committed",
            "data": results["q_bp_committed"].loc[:, node],
        },{
            "label": "Bypass Ramp Down",
            "unit": "CFS",
            "internal_key": "q_bp_ramp_down",
            "data": results["q_bp_ramp_down"].loc[:, node],
        },{
            "label": "Bypass Ramp Up",
            "unit": "CFS",
            "internal_key": "q_bp_ramp_up",
            "data": results["q_bp_ramp_up"].loc[:, node],
        },{
            "label": "Bypass Ramp Down Change",
            "unit": "-",
            "internal_key": "q_bp_rr_down_change",
            "data": results["q_bp_rr_down_change"].loc[:, node],
        },{
            "label": "Bypass Ramp Up Change",
            "unit": "-",
            "internal_key": "q_bp_rr_up_change",
            "data": results["q_bp_rr_up_change"].loc[:, node],
        },{
            "label": "Gauge Flow",
            "unit": "CFS",
            "internal_key": "q_gg",
            "data": results["q_gg"].loc[:, node],
        },{
            "label": "Gauge Ramp Down",
            "unit": "CFS",
            "internal_key": "q_gg_ramp_down",
            "data": results["q_gg_ramp_down"].loc[:, node],
        },{
            "label": "Gauge Ramp Up",
            "unit": "CFS",
            "internal_key": "q_gg_ramp_up",
            "data": results["q_gg_ramp_up"].loc[:, node],
        },{
            "label": "In Flows",
            "unit": "CFS",
            "internal_key": "q_in_flow",
            "data": results["q_in_flow"].loc[:, node],
        },{
            "label": "Out Flows",
            "unit": "CFS",
            "internal_key": "q_out_flow",
            "data": results["q_out_flow"].loc[:, node],
        },{
            "label": "Sink",
            "unit": "CFS",
            "internal_key": "q_sink",
            "data": results["q_sink"].loc[:, node],
        },{
            "label": "Source",
            "unit": "CFS",
            "internal_key": "q_source",
            "data": results["q_source"].loc[:, node],
        },{
            "label": "Total Ramp Down",
            "unit": "CFS",
            "internal_key": "q_tot_ramp_down",
            "data": results["q_tot_ramp_down"].loc[:, node],
        },{
            "label": "Total Ramp Up",
            "unit": "CFS",
            "internal_key": "q_tot_ramp_up",
            "data": results["q_tot_ramp_up"].loc[:, node],
        },{
            "label": "Turbine Ramp Down",
            "unit": "CFS",
            "internal_key": "q_tur_ramp_down",
            "data": results["q_tur_ramp_down"].loc[:, node],
        },{
            "label": "Turbine Ramp Up",
            "unit": "CFS",
            "internal_key": "q_tur_ramp_up",
            "data": results["q_tur_ramp_up"].loc[:, node],
        }])




    HEADER_FORMAT = workbook.add_format({
        'bold': True, 
        'font_color': 'black', 
        'bg_color': '#D9E1F2',
        'border': 1,
        'valign': 'vcenter',
        'align': 'center',
        'text_wrap': True,
    })

    UNIT_FORMAT = workbook.add_format({
        'bold': True, 
        'valign': 'vcenter',
        'align': 'center',
    })

    RESULTS_TABLE_OFFSET = (0, 0)


    for node in RESULT_NODES:
        worksheet = workbook.add_worksheet(f'Results | {node}')
        worksheet.write(0, 0, f'Results for {node}', HEADER_FORMAT)
        columns = COLUMN_MAP[node]

        data_start_row = RESULTS_TABLE_OFFSET[0] + 5
        data_start_col = RESULTS_TABLE_OFFSET[1]

        worksheet.set_row(RESULTS_TABLE_OFFSET[0], 60)

        for i, column in enumerate(columns):
            worksheet.write(
                RESULTS_TABLE_OFFSET[0], 
                RESULTS_TABLE_OFFSET[1] + i, 
                column["label"], 
                HEADER_FORMAT
            )

            worksheet.write(
                RESULTS_TABLE_OFFSET[0] + 1,
                RESULTS_TABLE_OFFSET[1] + i,
                column["unit"],
                UNIT_FORMAT
            )

            worksheet.add_sparkline(
                RESULTS_TABLE_OFFSET[0] + 2,
                RESULTS_TABLE_OFFSET[1] + i,
                {
                    'range': xl_range(
                        data_start_row, 
                        data_start_col + i, 
                        data_start_row + len(column["data"]) - 1, 
                        data_start_col + i
                    ),
                }
            )

            # Write the total value for that column
            if "include_total" in column and column["include_total"]:
                worksheet.write(
                    RESULTS_TABLE_OFFSET[0] + 3,
                    RESULTS_TABLE_OFFSET[1] + i,
                    np.sum(column["data"]),
                )
            else:
                worksheet.write(
                    RESULTS_TABLE_OFFSET[0] + 3,
                    RESULTS_TABLE_OFFSET[1] + i,
                    "-",
                )

            worksheet.write(
                data_start_row - 1,
                data_start_col + i,
                column["internal_key"], 
                HEADER_FORMAT
            )

            worksheet.write_column(
                data_start_row,
                data_start_col + i,
                column["data"]
            )

        worksheet.add_table(
            data_start_row - 1,
            data_start_col,
            data_start_row - 1 + len(column["data"]),
            data_start_col + len(columns) - 1,
            {
                'columns': [{'header': col["internal_key"]} for col in columns],
                'name': f'SummaryTable_{node}',
                'style': 'Table Style Medium 2'
            }
        )

    worksheet = workbook.add_worksheet('Plots')


    # worksheet.insert_image(0, 0, "/Users/marisusis/Documents/ANL/wapalib/weekly_model/TempRegPy/Results/Week10_WD_alt2/plot.png")
    # worksheet.insert_image(10, 10, "/Users/marisusis/Documents/ANL/wapalib/weekly_model/TempRegPy/Results/Week10_WD_alt2/pload_serving.png")

    workbook.close()