import xlsxwriter
from xlsxwriter.utility import xl_range
import numpy as np
import pandas as pd
import os


def draw_table(workbook, worksheet, name, columns, position):
    
    HEADER_FORMAT = workbook.add_format({
        'bold': True, 
        'font_color': 'black', 
        'bg_color': '#D9E1F2',
        'bottom': 2,
        'bottom_color': 'black',
        'top': 2,
        'top_color': 'black',
        'valign': 'vcenter',
        'align': 'center',
        'text_wrap': True,
    })

    UNIT_FORMAT = workbook.add_format({
        'bold': True, 
        'valign': 'vcenter',
        'align': 'center',
    })

    data_start_row = position[0] + 5
    data_start_col = position[1]

    worksheet.set_row(position[0], 60)

    for i, column in enumerate(columns):
        worksheet.write(
            position[0], 
            position[1] + i, 
            column["label"], 
            HEADER_FORMAT
        )

        worksheet.write(
            position[0] + 1,
            position[1] + i,
            column["unit"],
            UNIT_FORMAT
        )

        worksheet.add_sparkline(
            position[0] + 2,
            position[1] + i,
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
                position[0] + 3,
                position[1] + i,
                np.sum(column["data"]),
            )
        else:
            worksheet.write(
                position[0] + 3,
                position[1] + i,
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
        data_start_row - 1 + len(columns[0]["data"]),
        data_start_col + len(columns) - 1,
        {
            'columns': [{'header': col["internal_key"]} for col in columns],
            'name': f'SummaryTable_{name}',
            'style': 'Table Style Medium 2'
        }
    )

def draw_single_table(workbook, worksheet, data, position):

    LABEL_WIDTH = 2
    VALUE_WIDTH = 3

    HEADER_FORMAT = workbook.add_format({
        'bold': True, 
        'font_color': 'black', 
        'bg_color': '#D9E1F2',
        'bottom': 2,
        'bottom_color': 'black',
        'top': 2,
        'top_color': 'black',
        'valign': 'vcenter',
        'align': 'center',
        'text_wrap': True,
    })

    worksheet.set_row(position[0], 20)
    
    worksheet.merge_range(
        position[0], position[1],
        position[0], position[1] + LABEL_WIDTH - 1,
        "Label",
        HEADER_FORMAT
    )

    worksheet.merge_range(
        position[0], position[1] + LABEL_WIDTH,
        position[0], position[1] + LABEL_WIDTH + VALUE_WIDTH - 1,
        "Data",
        HEADER_FORMAT
    )

    for i, d in enumerate(data):
        worksheet.merge_range(
            position[0] + 1 + i, position[1],
            position[0] + 1 + i, position[1] + LABEL_WIDTH - 1,
            d["label"],
            workbook.add_format({
                'bold': True, 
                'font_color': 'black', 
                'right': 2,
                'right_color': 'black',
                # 'top': 1,
                # 'top_color': 'black',
                # 'bottom': 1,
                # 'bottom_color': 'black',
                'valign': 'vcenter',
                'align': 'left',
                'text_wrap': True,
            })
        )

        worksheet.merge_range(
            position[0] + 1 + i, position[1] + LABEL_WIDTH,
            position[0] + 1 + i, position[1] + LABEL_WIDTH + VALUE_WIDTH - 1,
            d["data"],
        )

    # worksheet.merge_range(
    #     DAILY_TABLE_ORIGIN[0]-2, 0, 
    #     DAILY_TABLE_ORIGIN[0]-1, 4,
    #     f'Daily values',
    #     table_title_format
    # )

    pass

def append_input_sheet(excel, workbook):
    worksheet = workbook.add_worksheet("Inputs")

    START_TIMESTAMP = pd.to_datetime(excel.loc[10, "Single input"])

    KEY_VAR = "Python Variable Names"

    D_INDEX = np.arange(1, 8, 1)
    H_INDEX = np.arange(1, 7 * 24 + 1, 1)

    SINGLE_COLUMNS = []
    DAILY_COLUMNS = [{
        "label": "Timestamp",
        "unit": "-",
        "internal_key": "timestamp",
        "data": [timestamp.strftime("%Y-%m-%d %H:%M") for timestamp in pd.date_range(
            start=START_TIMESTAMP,
            periods= 7,
            freq='h'
        )],
    },{
        "label": "Hour",
        "unit": "-",
        "internal_key": "hour",
        "data": np.linspace(1, 7, 7),
    }]
    HOURLY_COLUMNS = [{
        "label": "Timestamp",
        "unit": "-",
        "internal_key": "timestamp",
        "data": [timestamp.strftime("%Y-%m-%d %H:%M") for timestamp in pd.date_range(
            start=START_TIMESTAMP,
            periods= 7 * 24,
            freq='h'
        )],
    },{
        "label": "Hour",
        "unit": "-",
        "internal_key": "hour",
        "data": np.linspace(1, 7 * 24, 7 * 24),
    }]



    for python_key in excel.loc[:, KEY_VAR]:
        single = excel.loc[excel[KEY_VAR] == python_key, "Single input"]
        
        if single.empty or pd.isna(single.iloc[0]):
            data = excel.loc[excel[KEY_VAR] == python_key, "H01":"H168"]
            # Count the non-null values in the hourly data row
            actual_values = data.values.flatten()
            count_actual = np.count_nonzero(~pd.isnull(actual_values))
            if count_actual == 7:
                DAILY_COLUMNS.append({
                    "label" : excel.loc[excel[KEY_VAR] == python_key, "Glen Canyon Dam Inputs"].iloc[0],
                    "unit" : "-",
                    "internal_key": python_key,
                    "data": data.iloc[0, :7].values
                })
            elif count_actual == 168:
                HOURLY_COLUMNS.append({
                    "label" : excel.loc[excel[KEY_VAR] == python_key, "Glen Canyon Dam Inputs"].iloc[0],
                    "unit" : "-",
                    "internal_key": python_key,
                    "data": data.iloc[0, :168].values
                })

        
        else:
            data = single.iloc[0]
            label = excel.loc[excel[KEY_VAR] == python_key, "Glen Canyon Dam Inputs"]

            if "Simulation options" in label.values:
                # Skip simulation options
                continue
            
            SINGLE_COLUMNS.append({
                "label": label.iloc[0] if not label.empty else python_key,
                "unit": "-",
                "internal_key": python_key,
                "data": data,
            })

    SINGLE_TABLE_ORIGIN = np.array((0, 0))
    
    DAILY_TABLE_ORIGIN = SINGLE_TABLE_ORIGIN + np.array([1, 0]) * len(SINGLE_COLUMNS) + np.array([5, 0])
    HOURLY_TABLE_ORIGIN = DAILY_TABLE_ORIGIN + np.array([1, 0]) * 8 + np.array([8, 0])

    table_title_format = workbook.add_format({
        'bold': True,
        'font_color': 'black',
        'font_size': 16,
        'bg_color': '#d9d9d9',
        'bottom': 2,
        'bottom_color': 'black',
        'valign': 'vcenter',
        'align': 'center',
    })

    draw_single_table(
        workbook,
        worksheet,
        SINGLE_COLUMNS,
        SINGLE_TABLE_ORIGIN
    )

    worksheet.merge_range(
        DAILY_TABLE_ORIGIN[0]-2, 0, 
        DAILY_TABLE_ORIGIN[0]-1, 4,
        f'Daily Inputs',
        table_title_format
    )

    draw_table(workbook, worksheet, "daily", DAILY_COLUMNS, DAILY_TABLE_ORIGIN)

    worksheet.merge_range(
        HOURLY_TABLE_ORIGIN[0]-2, 0,
        HOURLY_TABLE_ORIGIN[0]-1, 4,
        f'Hourly Inputs',
        table_title_format
    )

    draw_table(workbook, worksheet, "hourly", HOURLY_COLUMNS, HOURLY_TABLE_ORIGIN)
    worksheet.set_column(0, 0, 15)

def export_results_to_excel(excel, inputs, results, file_path, include_plots=True):
    workbook = xlsxwriter.Workbook(file_path)

    START_TIMESTAMP = excel.loc[10,"Single input"]

    

    RESULT_NODES = ["GCD", "RM61"]
    COLUMN_MAP = {}

    for node in RESULT_NODES:
        COLUMN_MAP[node] = BASE_COLUMNS = [{
            "label": "Timestamp",
            "unit": "-",
            "internal_key": "timestamp",
            "data": [timestamp.strftime("%Y-%m-%d %H:%M") for timestamp in pd.date_range(
                start=START_TIMESTAMP,
                periods=len(results["p_tur"]),
                freq='h'
            )],
        },{
            "label": "Hour",
            "unit": "-",
            "internal_key": "hour",
            "data": np.linspace(1, len(results["p_tur"]), len(results["p_tur"])),
        },{
            "label": "Turbine Release",
            "unit": "CFS",
            "internal_key": "q_tur",
            "data": results["q_tur"].loc[:, node],
            "include_total": True,
        },{
            "label": "Bypass Release",
            "unit": "CFS",
            "internal_key": "q_bp",
            "data": results["q_bp"].loc[:, node],
            "include_total": True,
        },{
            "label": "Plant Temperature",
            "unit": "°C",
            "internal_key": "T_plant",
            "data": results["T_plant"].loc[:, node],
        },{
            "label": "Total Release",
            "unit": "CFS",
            "internal_key": "q_tot",
            "data": results["q_tot"].loc[:, node],
        },{
            "label": "Bypass Temperature",
            "unit": "°C",
            "internal_key": "T_bp_values",
            "data": inputs["T_bp_values"].loc["GCD"]
        },{
            "label": "Turbine Temperature",
            "unit": "°C",
            "internal_key": "T_tur_values",
            "data": inputs["T_tur_values"].loc["GCD"]
        },{
            "label": "Min Temperature @ RM61",
            "unit": "°C",
            "internal_key": "T_gauge_hourly_min_values",
            "data": inputs["T_gauge_hourly_min_values"].loc["RM61"]
        },{
            "label": "Max Temperature @ RM61",
            "unit": "°C",
            "internal_key": "T_gauge_hourly_max_values",
            "data": inputs["T_gauge_hourly_max_values"].loc["RM61"]
        },{
            "label": "∆T between GCD and RM61",
            "unit": "°C",
            "internal_key": "dT_hourly_values",
            "data": inputs["dT_hourly_values"].loc["GCD - RM61"]
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
        },{
            "label": "Location Marginal Price",
            "unit": "USD/MWh??",
            "internal_key": "lmp",
            "data": inputs["LMP_values"].loc["Node 1"]
        }]

    DAILY_COLUMNS = [{
        "label": "Timestamp",
        "unit": "-",
        "internal_key": "timestamp",
        "data": [timestamp.strftime("%Y-%m-%d %H:%M") for timestamp in pd.date_range(
            start=START_TIMESTAMP,
            periods=7,
            freq='d'
        )]
    },{
        "label": "Day",
        "unit": "-",
        "internal_key": "day",
        "data": np.arange(1, 8),
    },{
        "label": "Total Flow",
        "unit": "AF",
        "internal_key": "Q_tot_daily",
        "data": inputs["Q_tot_daily"].loc["GCD"],
    },{
        "label": "Maximum Daily Flow Change",
        "unit": "CFS",
        "internal_key": "Q_max_daily_change",
        "data": inputs["Q_max_daily_change"].loc["GCD"],
    },{
        "label": "Maximum Average Temperature @ RM61",
        "unit": "°C",
        "internal_key": "T_gauge_daily",
        "data": inputs["T_gauge_daily"].loc["RM61"],
    },{
        "label": "Difference between GCD and RM61",
        "unit": "°C",
        "internal_key": "dT_daily",
        "data": inputs["dT_daily"].loc["GCD - RM61"],
    },{
        "label": "Water/Power Conversion",
        "unit": "CFS/MW",
        "internal_key": "water_power_conversion",
        "data": inputs["WaterToPowerConversion"].loc["GCD"],
    }]

    

    DAILY_TABLE_ORIGIN = (2, 0)
    HOURLY_TABLE_ORIGIN = (20, 0)

    for node in RESULT_NODES:
        worksheet = workbook.add_worksheet(f'Results | {node}')
        worksheet.write(0, 0, f'Results for {node}')
        columns = COLUMN_MAP[node]

        
        
        table_title_format = workbook.add_format({
                'bold': True,
                'font_color': 'black',
                'font_size': 16,
                'bg_color': '#d9d9d9',
                'bottom': 2,
                'bottom_color': 'black',
                'valign': 'vcenter',
                'align': 'center',
        })

        worksheet.merge_range(
            DAILY_TABLE_ORIGIN[0]-2, 0, 
            DAILY_TABLE_ORIGIN[0]-1, len(DAILY_COLUMNS) - 1,
            f'Daily Values ({node})',
            table_title_format
        )

        draw_table(workbook, worksheet, f"Daily_{node}", DAILY_COLUMNS, (2, 0))


        worksheet.merge_range(
            HOURLY_TABLE_ORIGIN[0] - 2, 0,
            HOURLY_TABLE_ORIGIN[0] - 1, len(DAILY_COLUMNS) - 1,
            f'Hourly Values ({node})',
            table_title_format
        )
        draw_table(workbook, worksheet, node, columns, HOURLY_TABLE_ORIGIN)

        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 4)


    append_input_sheet(excel, workbook)

    if include_plots:
        worksheet = workbook.add_worksheet("Plots")

        worksheet.insert_image(0, 0, inputs["sim_folder"] + "/plot.png.png")
        worksheet.insert_image(30, 0, inputs["sim_folder"] + "/pload_serving.png.png")

    workbook.close()