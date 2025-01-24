import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import calendar

path = 'C:\\Users\\mpavicevic\\OneDrive - Argonne National Laboratory\\Research\\Papers\\Bypass-tool\\temp_lookup_table.xlsx'
df = pd.read_excel(path, sheet_name='Monthly', header=2, index_col=0)
df.dropna(inplace=True, axis=0, how='all')
df = df.loc[:, ['Month','Hour', '10°C', '10.5°C', '11°C', '11.5°C', '12°C', '12.5°C', '13°C', '13.5°C','14°C']]


##################
# Filter the DataFrame for only the months of July, August, and September
filtered_df = df[df['Month'].isin([7, 8, 9])]

# Set up the figure for subplots
months = filtered_df['Month'].unique()
num_months = len(months)

fig, axes = plt.subplots(nrows=num_months, ncols=1, figsize=(10, num_months * 4), sharex=True)

# Generate heatmaps for each month and find the overall min/max for color normalization
vmin = filtered_df[['10°C', '10.5°C', '11°C', '11.5°C', '12°C', '12.5°C', '13°C', '13.5°C', '14°C']].min().min()
vmax = filtered_df[['10°C', '10.5°C', '11°C', '11.5°C', '12°C', '12.5°C', '13°C', '13.5°C', '14°C']].max().max()

# Generate heatmaps for each month
for i, month in enumerate(months):
    month_data = filtered_df[filtered_df['Month'] == month]
    heatmap_data = month_data[
        ['Hour', '10°C', '10.5°C', '11°C', '11.5°C', '12°C', '12.5°C', '13°C', '13.5°C', '14°C']].set_index('Hour')

    # Reverse the heatmap data to match the y-tick labels
    heatmap_data_reversed = heatmap_data.iloc[::-1]  # Reverse the rows

    # Create a heatmap
    cax = axes[i].imshow(heatmap_data_reversed.T, aspect='auto', cmap='coolwarm', vmin=vmin, vmax=vmax,
                         interpolation='nearest')
    axes[i].set_title(f'{calendar.month_name[month]}', fontsize=16)
    axes[i].set_ylabel('Release temperature', fontsize=14)
    axes[i].set_yticks(range(len(heatmap_data.columns)))

    # Set y-tick labels in reverse order
    axes[i].set_yticklabels(heatmap_data.columns[::-1])  # Reverse the labels

# Add a single colorbar for all subplots
cbar = fig.colorbar(cax, ax=axes, orientation='vertical', fraction=0.02, pad=0.04, aspect=40, shrink=1.3)
cbar.set_label(r'$\Delta T_{GCD,RM15}$ (°C)', fontsize=14)

# Set the x-axis labels
axes[-1].set_xlabel('Hour of Day', fontsize=14)
plt.xticks(ticks=range(0, 24), labels=range(0, 24), rotation=0)

plt.tight_layout(rect=[0, 0, 0.88, 1])
plt.show()


#########################
df = pd.read_excel(path, sheet_name='Daily', header=2, index_col=0)
df = df.loc[:, ['10°C', '10.5°C', '11°C', '11.5°C', '12°C', '12.5°C', '13°C', '13.5°C','14°C']]

# Ensure the Datetime index is a datetime object
df.index = pd.to_datetime(df.index)

# Initialize a dictionary to hold the warmest days for each month
warmest_days = {}

# Loop through each month (1 to 12)
for month in range(6, 11):
    # Filter DataFrame for the specific month
    monthly_data = df[df.index.month == month]

    # Group by day and calculate the mean temperature for each day
    daily_avg = monthly_data.resample('D').mean()

    # Find the day with the highest average temperature
    warmest_day = daily_avg.idxmax()  # Gets the index of the max average temperature
    warmest_days[month] = warmest_day  # Store the warmest day for that month

# Now extract the 24-hour period for each warmest day
warmest_periods = {}
for month, warmest_day in warmest_days.items():
    # Ensure the warmest_day is indeed in the index
    if warmest_day in df.index:
        # Get the 24-hour data for the warmest day
        warmest_period = df[warmest_day: warmest_day + pd.Timedelta(hours=24)]
        warmest_periods[month] = warmest_period
    else:
        print(f"No data available for warmest day {warmest_day} in month {month}")

# Example output for a specific month
for month, data in warmest_periods.items():
    print(f"Warmest 24-hour period for month {month}:\n", data)

# Create subplots for each month
fig, axs = plt.subplots(len(months), 1, figsize=(12, len(months) * 4), sharex=True)

for i, month in enumerate(months):
    # Filter DataFrame for the specific month
    monthly_data = df[df.index.month == month]

    # Transpose the DataFrame for heatmap plotting
    data = monthly_data.T

    # Create the heatmap
    cax = axs[i].imshow(data, aspect='auto', cmap='viridis', interpolation='nearest')

    # Set ticks and labels
    axs[i].set_xticks(np.arange(len(monthly_data.index)))
    axs[i].set_xticklabels(monthly_data.index.strftime('%Y-%m-%d'), rotation=45)
    axs[i].set_yticks(np.arange(len(df.columns)))
    axs[i].set_yticklabels(df.columns)

    # Add title for each subplot
    axs[i].set_title(f'Temperature Heatmap for Month: {month}')

# Add color bar to the figure
cbar = fig.colorbar(cax, ax=axs, orientation='vertical', pad=0.02)
cbar.set_label('Temperature (°C)')

# Customize the plot
plt.xlabel('Datetime')
plt.ylabel('Temperature (°C)')
plt.tight_layout()  # Adjust layout to prevent clipping
plt.show()