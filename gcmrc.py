"""
The TempRegPy module
"""
from numpy.version import release

import tempregpy as trp
import pandas as pd

# Load the Excel file
file_path = 'C:\\Projects\\GitHub\\TempRegPy\\TempRegPy_GCD_LoadDriven.xlsm'
config = trp.load_config(file_path)


date_range = pd.date_range(start='01/01/2025', end='31/12/2025', freq='h')
df_hourly_data = pd.DataFrame(index=date_range)
date_range = pd.date_range(start='01/01/2025', end='31/12/2025', freq='d')
df_daily = pd.DataFrame(index=date_range)
#%%%
# Bypass Release #
df_hourly_data['Q_bp_max_values'] = 15000
Q_bp_start_date = pd.to_datetime('01/01/2025', dayfirst=True)
Q_bp_end_date = pd.to_datetime('20/07/2025', dayfirst=True)
df_hourly_data.loc[(df_hourly_data.index >= Q_bp_start_date) & (df_hourly_data.index <= Q_bp_end_date), 'Q_bp_max_values'] = 7500

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
    df_hourly_data.loc[(df_hourly_data.index >= start_date) & (df_hourly_data.index < end_date), 'Q_tur_max_values'] = value

# Handle the last range separately
last_start_date, last_value = Q_tur_max_dates[-1]
df_hourly_data.loc[df_hourly_data.index >= last_start_date, 'Q_tur_max_values'] = last_value

df_hourly = {'Q_tur_max_values': df_hourly_data['Q_tur_max_values'],
             'Q_bp_max_values': df_hourly_data['Q_bp_max_values']}

#%%
# Daily data
folder_path = 'C:\\Users\\mpavicevic\\OneDrive - Argonne National Laboratory\\Projects\\SMB EIS\\GCMRC\\Inputs for Optimization Tool\\'
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
#Run simulation
inputs, results, duals = trp.build_and_run(config)

print('A')