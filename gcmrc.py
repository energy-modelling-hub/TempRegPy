"""
The TempRegPy module
"""
from numpy.version import release

import tempregpy as trp
import pandas as pd

# Load the Excel file
file_path = 'C:\\Projects\\GitHub\\TempRegPy\\TempRegPy_GCD_LoadDriven.xlsm'
config = trp.load_config(file_path)

#%%
folder_path = 'C:\\Users\\mpavicevic\\OneDrive - Argonne National Laboratory\\Projects\\SMB EIS\\GCMRC\\Inputs for Optimization Tool\\'

# Dates
dates = pd.read_csv(folder_path + 'Dates.csv', parse_dates=True)
date_columns = [f'X{year}' for year in range(2020, 1990, -1)]
dates[date_columns] = dates[date_columns].apply(pd.to_datetime, format='%m/%d/%Y', errors='coerce')
dates.loc[dates['Type'] == 'EndDate', date_columns] += pd.Timedelta(hours=23)
dates.loc[dates['Type'] == 'StartDate', date_columns] += pd.Timedelta(hours=0)

#%%

date_range = pd.date_range(start='01/01/2025', end='31/12/2025', freq='h')
df_hourly_static = pd.DataFrame(index=date_range)
date_range = pd.date_range(start='01/01/2025', end='31/12/2025', freq='d')
df_daily = pd.DataFrame(index=date_range)
#%%%
# Bypass Release #
df_hourly_static['Q_bp_max_values'] = 15000
Q_bp_start_date = pd.to_datetime('01/01/2025', dayfirst=True)
Q_bp_end_date = pd.to_datetime('20/07/2025', dayfirst=True)
df_hourly_static.loc[(df_hourly_static.index >= Q_bp_start_date) & (df_hourly_static.index <= Q_bp_end_date), 'Q_bp_max_values'] = 7500

#%%%
# Turbine Release #
Q_tur_max_dates = [
    ('01/01/2025', 16100),
    ('03/03/2025', 19700),
    ('07/04/2025', 23300),
    ('12/05/2025', 26900),
    ('01/09/2025', 19700),
    ('06/10/2025', 19650),
    ('03/11/2025', 26850)
]

# Convert date strings to datetime objects
Q_tur_max_dates = [(pd.to_datetime(date, dayfirst=True), value) for date, value in Q_tur_max_dates]

# Update the 'Q_bp_max_values' column for each range
for i in range(len(Q_tur_max_dates) - 1):
    start_date, value = Q_tur_max_dates[i]
    end_date, _ = Q_tur_max_dates[i + 1]
    df_hourly_static.loc[(df_hourly_static.index >= start_date) & (df_hourly_static.index < end_date), 'Q_tur_max_values'] = value

# Handle the last range separately
last_start_date, last_value = Q_tur_max_dates[-1]
df_hourly_static.loc[df_hourly_static.index >= last_start_date, 'Q_tur_max_values'] = last_value

df_hourly = {'Q_tur_max_values': df_hourly_static['Q_tur_max_values'],
             'Q_bp_max_values': df_hourly_static['Q_bp_max_values']}

#%%
# Daily data
file_release = 'April 2025 CRMMS Results Lake Powell Pool Release Volume.csv'
data_release = pd.read_csv(folder_path+file_release, index_col=0, parse_dates=True).iloc[:,6:]
data_release = data_release.loc[data_release.index < pd.to_datetime('01/01/2026',dayfirst=True),:]

def calculate_max_daily_change(date, af_value):
    month = date.month
    if month in [6, 7, 8]:  # June, July, August
        factor = 9 / 1000
    else:
        factor = 10 / 1000
    max_daily_change = af_value * factor
    return min(max_daily_change, 8000)

df_max_daily_change = pd.DataFrame(index=data_release.index)
for year in data_release.columns:
    df_max_daily_change[year] = data_release[year].index.to_series().apply(
        lambda date: calculate_max_daily_change(date, data_release.at[date, year])
    )
df_daily = {'Q_max_daily_change': df_max_daily_change.resample('D').ffill()}
df_daily['Q_max_daily_change'].columns = ['X' + str(col) for col in df_daily['Q_max_daily_change'].columns]

df_daily['Q_tot_daily'] = data_release.resample('D').ffill()
days_in_month = df_daily['Q_tot_daily'].index.days_in_month
df_daily['Q_tot_daily'] = df_daily['Q_tot_daily'].div(days_in_month, axis=0)
df_daily['Q_tot_daily'].columns = ['X' + str(col) for col in df_daily['Q_tot_daily'].columns]

#%%
file_elevation = 'April 2025 CRMMS Results Lake Powell Pool Elevation.csv'
data_elevation = pd.read_csv(folder_path+file_elevation, index_col=0, parse_dates=True).iloc[:,6:]
data_elevation = data_elevation.loc[data_elevation.index <= pd.to_datetime('31/12/2025',dayfirst=True),:]
data_elevation.index = data_elevation.index + pd.offsets.MonthEnd(0)
daily_elevation = data_elevation.resample('D')
daily_elevation = daily_elevation.interpolate(method='linear')
daily_elevation.columns = ['X' + str(col) for col in daily_elevation.columns]

df_daily['WaterToPowerConversion'] = (0.0009948396260262412*daily_elevation-1.1324182069242603e-7*df_daily['Q_tot_daily']-3.143005865356586)/12.1
df_daily['WaterToPowerConversion'] = df_daily['WaterToPowerConversion'].where(
    df_daily['WaterToPowerConversion'] > 0.36/12.1, 0.36/12.1
)
df_daily['WaterToPowerConversion'] = df_daily['WaterToPowerConversion'].where(
    df_daily['WaterToPowerConversion'] < 0.48/12.1, 0.48/12.1
)

#%%
data_demand = pd.read_excel(folder_path + 'CRMMS_GC_Hourly_cfs_report.xlsx', sheet_name='MWh', parse_dates=True)
data_demand['Date'] = pd.to_datetime(data_demand['Date'])
data_demand['Datetime'] = data_demand.apply(lambda row: row['Date'] + pd.Timedelta(hours=row['Hour'] - 1), axis=1)
data_demand.set_index('Datetime', inplace=True)
data_demand.drop(columns=['Date', 'Hour'], inplace=True)
df_hourly['Demand_values'] = data_demand
df_hourly['LMP_values'] = data_demand

#%%
df_daily['dT_daily'] = {}
df_hourly['dT_hourly_values'] = {}

for i in ['0', '15', '30', '61']:
    dt_name = f'deltatemp_{i}.csv'
    data_dt = pd.read_csv(folder_path+dt_name)
    data_dt.index = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    df_daily['dT_daily'][i] = data_dt.copy()
    df_hourly['dT_hourly_values'][i] = data_dt.resample('h').ffill()

for j in ['GCD']:
    bp_name = f'by_temp_{j}.csv'
    tur_name = f'pen_temp_{j}.csv'
    data_bp = pd.read_csv(folder_path + bp_name)
    data_bp.index = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    df_hourly['T_bp_values'] = data_bp.resample('h').ffill()
    data_tur = pd.read_csv(folder_path + tur_name)
    data_tur.index = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    df_hourly['T_tur_values'] = data_tur.resample('h').ffill()
    temp = df_hourly['T_tur_values'].copy()
    temp = temp.where(temp < 15.5, 15.5)

    df_hourly['T_gauge_hourly_max_values'] = temp + 4
    df_hourly['T_gauge_hourly_min_values'] = temp - 3


#%%
import numpy as np
inputs, results, duals = {}, {}, {}
cfs_to_af = 1/12.1
# for rm in [0, 15, 30, 61]:
for rm in [61]:
    inputs[rm], results[rm], duals[rm] = {}, {}, {}
    trace_list = [f"X{year}" for year in range(2020, 1991 - 1, -1)]
    for trace in trace_list:
        # inputs[rm][trace], results[rm][trace], duals[rm][trace] = {}, {}, {}
        if not np.isnat(dates.loc[(dates['RM'] == rm) & (dates['Type'] == 'StartDate'), trace].values[0]):
            start_date = dates.loc[(dates['RM'] == rm) & (dates['Type'] == 'StartDate'), trace].values[0]
            end_date = dates.loc[(dates['RM'] == rm) & (dates['Type'] == 'EndDate'), trace].values[0]
            selected_dates = pd.date_range(start=pd.to_datetime(start_date), end=pd.to_datetime(end_date))
            for date in selected_dates:
                scenario = f'RM{rm}\\{trace}\\{date.strftime("%Y-%m-%d")}'
                config['sim_folder'] = scenario
                ### Single input
                config['Q_tot_daily'].loc['GCD','Single input'] = df_daily['Q_tot_daily'].loc[date,trace]
                config['Q_max_daily_change'].loc['GCD','Single input'] = df_daily['Q_max_daily_change'].loc[date,trace]*cfs_to_af
                config['WaterToPowerConversion'].loc['GCD', 'Single input'] = df_daily['WaterToPowerConversion'].loc[date,trace]/cfs_to_af
                config['dT_daily'].loc['GCD - RM61', 'Single input'] = df_daily['dT_daily'][str(rm)].loc[date, trace]
                ### 24H inputs static
                config['Q_bp_max_values'].loc['GCD', :] = df_hourly['Q_bp_max_values'].loc[date.strftime("%Y-%m-%d")].values*cfs_to_af
                config['Q_tur_max_values'].loc['GCD', :] = df_hourly['Q_tur_max_values'].loc[date.strftime("%Y-%m-%d")].values*cfs_to_af
                ### 24H inputs per trace
                config['Demand_values'].loc['Node 1', :] = df_hourly['Demand_values'].loc[date.strftime("%Y-%m-%d"),trace].values
                config['LMP_values'].loc['Node 1', :] = df_hourly['LMP_values'].loc[date.strftime("%Y-%m-%d"),trace].values
                config['T_bp_values'].loc['GCD', :] = df_hourly['T_bp_values'].loc[date.strftime("%Y-%m-%d"),trace].values
                config['T_tur_values'].loc['GCD', :] = df_hourly['T_tur_values'].loc[date.strftime("%Y-%m-%d"), trace].values
                config['T_gauge_hourly_max_values'].loc['RM61', :] = df_hourly['T_gauge_hourly_max_values'].loc[date.strftime("%Y-%m-%d"), trace].values
                # config['T_gauge_hourly_min_values'].loc['RM61', :]=config['T_gauge_hourly_min_values'].loc['RM61', :].astype('float64')
                config['T_gauge_hourly_min_values'].loc['RM61', :] = df_hourly['T_gauge_hourly_min_values'].loc[date.strftime("%Y-%m-%d"), trace].values

                ### 24H inputs per river mile and trace
                config['dT_hourly_values'].loc['GCD - RM61', :] = df_hourly['dT_hourly_values'][str(rm)].loc[date.strftime("%Y-%m-%d"),trace].values
                inputs, results, duals = trp.build_and_run(config)

                # inputs[rm][trace][str(date)], results[rm][trace][str(date)], duals[rm][trace][str(date)] = trp.build_and_run(config)
#%%
#Run simulation
# inputs, results, duals = trp.build_and_run(config)
import os

def delete_app_log_files(base_directory):
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            # Check if the file is app.log
            if file == 'app.log':
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

# Specify the base directory where folderX is located
base_directory = 'C:\\Projects\\Github\\TempRegPy\\Results'

# Call the function
delete_app_log_files(base_directory)



#%%
import os
from datetime import datetime
import pandas as pd
# Define the root directory
root_dir = 'C:\\Projects\\Github\\TempRegPy\\Results'

# Initialize the main dictionary to store data
river_miles_data = {}

# Traverse the directory structure
for file in ['q_bp.csv', 'q_tur.csv']:
    river_miles_data[file] = {}
    for rm_folder in os.listdir(root_dir):
        rm_path = os.path.join(root_dir, rm_folder)
        if os.path.isdir(rm_path):
            # Initialize a dictionary for each river mile
            river_miles_data[file][rm_folder] = {}

            for trace_folder in os.listdir(rm_path):
                trace_path = os.path.join(rm_path, trace_folder)
                if os.path.isdir(trace_path):
                    # Initialize a dictionary for each trace
                    river_miles_data[file][rm_folder][trace_folder] = {}

                    for date_folder in os.listdir(trace_path):
                        date_path = os.path.join(trace_path, date_folder)
                        if os.path.isdir(date_path):
                            # Parse the date from the folder name
                            date = datetime.strptime(date_folder, '%Y-%m-%d')
                            river_miles_data[file][rm_folder][trace_folder][date] = {}
                            # Read each CSV file in the date folder
                            for csv_file in os.listdir(date_path):
                                if csv_file.endswith(file):
                                    file_path = os.path.join(date_path, csv_file)
                                    df = pd.read_csv(file_path)

                                    hourly_dates = pd.date_range(start=date, periods=24, freq='h')

                                    # Assign the hourly dates to the Date column
                                    df.index = hourly_dates

                                    # Store the DataFrame in the dictionary
                                    river_miles_data[file][rm_folder][trace_folder][date] = df.loc[:,'GCD']


results = {}
for f in river_miles_data.keys():
    results[f] = {}
    for rm in river_miles_data[f].keys():
        results[f][rm] = pd.DataFrame()
        for tr in river_miles_data[f][rm].keys():
            tmp = pd.concat(river_miles_data[f][rm][tr].values(), axis=0)
            df = pd.DataFrame(tmp.copy())
            df.columns = [tr]
            results[f][rm] = pd.concat([results[f][rm], df], axis=1)
        if f == 'q_bp.csv':
            var = 'q_bp'
        elif f == 'q_tur.csv':
            var = 'q_tur'
        # results[f][rm].to_csv(f'{var}_{rm}.csv', index=True)



import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10,5))
results['q_bp.csv']['RM0'].loc[:,['X2020','X1991']].plot(ax=ax)
plt.tight_layout()
plt.show()