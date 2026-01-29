"""
Full script to generate improved weekly‐horizon diagnostics (July → Nov):
  A) Monthly boxplots of daily‐mean temperature by scenario
  B) Daily violations by Day‐Type AND by Month
  C) Paired boxplots of daily total release vs. bypass‐share by month
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle as pkl

import numpy  as np
import pandas as pd
import pickle as pkl

# -----------------------------------------------------------------------------
# 1) Define your inputs
# -----------------------------------------------------------------------------
data = {
    "new_all": {
        "name": "OC",
        "file": (
            "C:\\Users\\mpavicevic\\Box\\TempRegPy\\Environmental_Modelling_&_Software_Paper\\2025-08-28 Updated CRiSPPy results\\"
            "Historical bypass, all plants optimized (ref case)\\"
            "database.pkl"
        ),
    },
    "new_gc": {
        "name": "OI",
        "file": (
            "C:\\Users\\mpavicevic\\Box\\TempRegPy\\Environmental_Modelling_&_Software_Paper\\2025-08-28 Updated CRiSPPy results\\"
            "Historical bypass, GC optimized, other plants fixed from ref case\\"
            "database.pkl"
        ),
    },
    "old_all": {
        "name": "PC",
        "file": (
            "C:\\Users\\mpavicevic\\Box\\TempRegPy\\Environmental_Modelling_&_Software_Paper\\2025-08-28 Updated CRiSPPy results\\"
            "2025-09-12 Flat bypass, all plants optimized\\"
            "database.pkl"
        ),
    },
    "old_gc": {
        "name": "PI",
        "file": (
            "C:\\Users\\mpavicevic\\Box\\TempRegPy\\Environmental_Modelling_&_Software_Paper\\2025-08-28 Updated CRiSPPy results\\"
            "2025-09-12 Flat bypass, GC optimized, other plants fixed from ref case\\"
            "database.pkl"
        ),
    },
}

# will collect each scenario here
df_list = []

# -----------------------------------------------------------------------------
# 2) Loop through each scenario, load, process, and store its DataFrame
# -----------------------------------------------------------------------------
for key, cfg in data.items():
    # 2.1) Load the pickle
    with open(cfg["file"], "rb") as f:
        datum = pkl.load(f)

    # 2.2) Extract Plant and Other results, reset_index so 'date' is a column
    plant_df = datum["dictOutput"]["PlantOutputResults"].reset_index()
    other_df = datum["dictOutput"]["OtherOutputResults"].reset_index()

    # 2.3) Concatenate vertically
    df = pd.concat([plant_df, other_df], ignore_index=True)

    # 2.4) Annotate with your scenario label (OC, OI, PC, PI)
    df["scenario"] = cfg["name"]

    # 2.5) Rename columns: 'datatype' → 'key', 0 → 'value'
    df = df.rename(columns={"datatype": "key", 0: "value"})

    # 2.6) Rebuild true timestamp: to_datetime(date) + hour hours
    df["date"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")

    # 2.7) We no longer need the 'hour' column once datetime is rebuilt
    df = df.drop(columns="hour")

    # 2.8) Sort by date & scenario
    df = df.sort_values(["date", "scenario", "key"])

    # 2.9) AGGREGATE duplicates: sum any repeated date+scenario+key
    #      (change aggfunc if needed: 'first', 'mean', etc.)
    df = (
        df
        .groupby(["date", "scenario", "key"], as_index=False)["value"]
        .sum()
    )

    # 2.10) Pivot so each key becomes a column
    df_wide = (
        df
        .pivot(index=["date", "scenario"], columns="key", values="value")
        .reset_index()
    )
    # clear the columns.name
    df_wide.columns.name = None

    # 2.11) Save to list
    df_list.append(df_wide)

# -----------------------------------------------------------------------------
# 3) Combine all scenarios into one big DataFrame
# -----------------------------------------------------------------------------
combined_df = pd.concat(df_list, ignore_index=True)

# set 'date' as index if you like
combined_df = combined_df.set_index("date").sort_index()

# -----------------------------------------------------------------------------
# 4) Inspect the result
# -----------------------------------------------------------------------------
print("All scenarios combined:")
print(combined_df.info())
print(combined_df.head())


# --------------------------------------------------------------------
# 1) Build date ranges (July 1 → November 30)
# --------------------------------------------------------------------
rng_hourly = pd.date_range("2023-07-01", "2023-11-30 23:00", freq="h")
rng_daily  = pd.date_range("2023-07-01", "2023-11-30",       freq="d")

np.random.seed(123)

# --------------------------------------------------------------------
# 2) Generate dummy hourly temperatures for four scenarios
# --------------------------------------------------------------------
scenarios = ["PI", "PC", "OI", "OC"]
temp_h = pd.DataFrame(index=rng_hourly, columns=scenarios, dtype=float)

for s in scenarios:
    temp_h[s] = (
        15.5
        + 1.0 * np.sin(2 * np.pi * (rng_hourly.hour + 24 * rng_hourly.dayofyear) / 24 / 7)
        + 0.7 * np.random.randn(len(rng_hourly))
    )

# Resample to daily means for cleaner boxplots
temp_d = temp_h.resample("d").mean()
temp_d["Month"] = temp_d.index.month_name().str[:3]  # 'Jul', 'Aug', ...

# --------------------------------------------------------------------
# 3) Generate dummy daily violations, total releases, bypass‐share
# --------------------------------------------------------------------
daily = pd.DataFrame(index=rng_daily)
daily["violations"] = np.random.poisson(lam=2.5, size=len(daily))

# Compute raw releases and clip to min=800 cfs
raw_release = (
    1000
    + 200 * np.sin(2 * np.pi * daily.index.dayofyear / 365)
    + 150 * np.random.randn(len(daily))
)
daily["releases"] = np.clip(raw_release, a_min=800, a_max=None)

# Dummy bypass share between 0 and 1
daily["bypass_share"] = np.random.beta(a=2, b=5, size=len(daily))

# Categorize day‐type
def day_type(dt):
    name = dt.day_name()
    if name in ("Saturday", "Sunday"):
        return name
    return "Weekday"

daily["DayType"] = daily.index.map(day_type)

# --------------------------------------------------------------------
# 4) Prepare plotting parameters
# --------------------------------------------------------------------
months     = ["Jul", "Aug", "Sep", "Oct", "Nov"]
month_nums = [7, 8, 9, 10, 11]  # numeric months
daytypes   = ["Weekday", "Saturday", "Sunday"]

# --------------------------------------------------------------------
# 5) Create the 3‐panel figure
# --------------------------------------------------------------------
fig, (axA, axB, axC) = plt.subplots(3, 1, figsize=(10, 16))
plt.subplots_adjust(hspace=0.45)

# --- Panel A: Temperature boxplots by month & scenario ---
width   = 0.15
x_month = np.arange(len(months))
offsets = np.linspace(-1.5*width, 1.5*width, len(scenarios))

for i, s in enumerate(scenarios):
    data = [temp_d.loc[temp_d.index.month==m, s].values for m in month_nums]
    pos  = x_month + offsets[i]
    axA.boxplot(
        data,
        positions=pos,
        widths=width,
        patch_artist=True,
        boxprops=dict(facecolor=f"C{i}", alpha=0.6),
        medianprops=dict(color="k"),
    )

axA.set_xticks(x_month)
axA.set_xticklabels(months)
axA.axhline(15.5, color="r", linestyle="--", label="15.5 °C Threshold")
axA.set_title("A) Daily‐Mean Temperature by Month & Scenario")
axA.set_ylabel("Temperature (°C)")
# Legend: scenarios + threshold
handles = [plt.Line2D([0],[0], color=f"C{i}", lw=8, alpha=0.6) for i in range(len(scenarios))]
handles.append(plt.Line2D([0],[0], color="r", lw=1.5, linestyle="--"))
labels = scenarios + ["Threshold"]
axA.legend(handles, labels, loc="upper left")
axA.grid(alpha=0.3)


# --- Panel B: Violations by Month + DayType ---
w       = 0.25
offsets = np.linspace(-w, w, len(daytypes))

for j, dt in enumerate(daytypes):
    # For each month, grab the violations of that day‐type
    data = [
        daily.loc[
            (daily.index.month==m) & (daily["DayType"]==dt),
            "violations"
        ].values
        for m in month_nums
    ]
    pos = x_month + offsets[j]
    axB.boxplot(
        data,
        positions=pos,
        widths=w/1.2,
        patch_artist=True,
        boxprops=dict(facecolor=f"C{j+3}", alpha=0.6),
        medianprops=dict(color="k"),
    )

axB.set_xticks(x_month)
axB.set_xticklabels(months)
axB.set_title("B) Daily Violations by Month & DayType")
axB.set_ylabel("Violation Count")
# Legend for daytypes
handles = [plt.Line2D([0],[0], color=f"C{j+3}", lw=8, alpha=0.6) for j in range(len(daytypes))]
axB.legend(handles, daytypes, loc="upper left")
axB.grid(alpha=0.3)


# --- Panel C: Monthly releases & bypass‐share paired boxplots ---
release_data = [
    daily.loc[daily.index.month==m, "releases"].values
    for m in month_nums
]
bypass_data  = [
    daily.loc[daily.index.month==m, "bypass_share"].values
    for m in month_nums
]

pos_rel = x_month - w/2
pos_byp = x_month + w/2

# Releases
axC.boxplot(
    release_data,
    positions=pos_rel,
    widths=w/1.2,
    patch_artist=True,
    boxprops=dict(facecolor="C1", alpha=0.6),
    medianprops=dict(color="k"),
)
axC.set_ylabel("Daily Total Release (cfs)", color="C1")
axC.tick_params(axis="y", labelcolor="C1")

# Bypass share on twin axis
axC2 = axC.twinx()
axC2.boxplot(
    bypass_data,
    positions=pos_byp,
    widths=w/1.2,
    patch_artist=True,
    boxprops=dict(facecolor="C2", alpha=0.6),
    medianprops=dict(color="k"),
)
axC2.set_ylabel("Bypass Share (fraction)", color="C2")
axC2.tick_params(axis="y", labelcolor="C2")

axC.set_xticks(x_month)
axC.set_xticklabels(months)
axC.set_title("C) Daily Total Release & Bypass Share by Month")
axC.grid(alpha=0.2)

# --------------------------------------------------------------------
# 6) Final touches
# --------------------------------------------------------------------
fig.suptitle("Improved Weekly‐Horizon Diagnostics (July → November)", fontsize=16, y=0.95)
plt.tight_layout()
plt.show()

#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Reproducible randomness
rng = np.random.default_rng(42)

# Hourly index for Jul–Nov 2024 (use 'h' to avoid FutureWarning)
idx = pd.date_range('2024-07-01', '2024-11-30 23:00', freq='h')
df = pd.DataFrame(index=idx)

# Helpers (use ndarray to avoid Index-specific behavior)
hour = df.index.hour.to_numpy()
dow  = df.index.dayofweek.to_numpy()  # 0=Mon ... 6=Sun
is_weekend = dow >= 5
month_num  = df.index.month.to_numpy()

# Monthly maps (means/bases)
temp_gcd_month_mean = {7:21.0, 8:20.5, 9:18.0, 10:14.0, 11:10.0}  # °C upstream
turbine_month_base  = {7:55000, 8:52000, 9:45000, 10:38000, 11:32000}  # cfs
bypass_month_base   = {7:7000,  8:6500,  9:4500,  10:3000,  11:2000}   # cfs
demand_month_base   = {7:1300,  8:1250,  9:1100,  10:1000,  11:950}    # MW
lmp_month_base      = {7:55,    8:50,    9:45,    10:40,    11:35}     # $/MWh
temp_target_month   = {7:17.0,  8:17.0,  9:16.0,  10:15.0,  11:13.0}   # °C

def map_month(dct):
    return np.array([dct[m] for m in month_num], dtype=float)

temp_gcd_base = map_month(temp_gcd_month_mean)
turbine_base  = map_month(turbine_month_base)
bypass_base   = map_month(bypass_month_base)
demand_base   = map_month(demand_month_base)
lmp_base      = map_month(lmp_month_base)
temp_target   = map_month(temp_target_month)

# Diurnal shapes
temp_diurnal = 0.7 * np.sin(2*np.pi*(hour - 15)/24.0)
temp_noise   = rng.normal(0, 0.3, size=len(df))

# Demand: morning and evening peaks
morning_peak = np.exp(-0.5 * ((hour - 8)/2.5)**2)
evening_peak = np.exp(-0.5 * ((hour - 18)/3.0)**2)
demand_shape = 0.5 + 0.6*(morning_peak + evening_peak)
demand_weekend_scale = np.where(is_weekend, 0.90, 1.00)
demand_noise = rng.normal(0, 30, size=len(df))

# Turbine release: higher on weekdays and during on-peak hours
turbine_diurnal = 0.85 + 0.35*np.sin(2*np.pi*(hour - 12)/24.0)**2
turbine_weekend_scale = np.where(is_weekend, 0.85, 1.00)
turbine_noise = rng.normal(0, 3000, size=len(df))

# Build variables (use np.clip instead of .clip(lower=...))
df['temp_GCD'] = np.clip(temp_gcd_base + temp_diurnal + temp_noise, 4.0, None)
df['demand']   = np.clip(demand_base * demand_shape * demand_weekend_scale + demand_noise, 200, None)

df['turbine_release'] = np.clip(turbine_base * turbine_diurnal * turbine_weekend_scale + turbine_noise, 15000, None)

# Bypass release
hot_bonus = np.clip((df['temp_GCD'] - 17.0) * 1500, 0, 4000)
bypass_weekend_scale = np.where(is_weekend, 1.10, 1.00)
bypass_noise = rng.normal(0, 800, size=len(df))
df['bp_release'] = np.clip(bypass_base * bypass_weekend_scale + hot_bonus + bypass_noise, 500, None)

# Total release (+ small random spillage/noise)
spill_noise = np.clip(rng.normal(300, 200, size=len(df)), 0, None)
df['total_release'] = df['turbine_release'] + df['bp_release'] + spill_noise

# Temperature at RM61
mix_fraction = df['bp_release'] / (df['bp_release'] + df['turbine_release'] + 1e-6)
cooling_max  = 4.5
deltaT_effect = cooling_max * mix_fraction
rm61_diurnal  = 0.1 * np.sin(2*np.pi*(hour - 15)/24.0)
rm61_noise    = rng.normal(0, 0.15, size=len(df))
df['temp_RM61'] = np.clip(df['temp_GCD'] - deltaT_effect + rm61_diurnal + rm61_noise, 2.0, None)

# Target temperature schedule
df['temp_target'] = temp_target

# Prices (LMP)
lmp_demand_coupling = 0.03 * (df['demand'] - 1000)
lmp_diurnal         = 3.0 * np.sin(2*np.pi*(hour - 16)/24.0)
lmp_weekend_disc    = np.where(is_weekend, -2.0, 0.0)
lmp_noise           = rng.normal(0, 4.0, size=len(df))
df['LMP'] = np.clip(lmp_base + lmp_demand_coupling + lmp_diurnal + lmp_weekend_disc + lmp_noise, 10.0, None)

# Add month/daytype to df (used in plots)
df['month']   = df.index.month_name().str[:3]
df['daytype'] = df.index.day_name().map(lambda d: d if d in ['Saturday','Sunday'] else 'Weekday')

# Daily aggregates
daily = df.resample('D').agg({
    'total_release': 'sum',
    'bp_release': 'sum',
    'turbine_release': 'sum',
    'LMP': 'mean',
    'demand': 'mean',
    'temp_RM61': 'mean',
    'temp_GCD': 'mean'
})
daily['violations'] = (df['temp_RM61'] > df['temp_target']).resample('D').sum()
daily['month']   = daily.index.month_name().str[:3]
daily['daytype'] = daily.index.day_name().map(lambda d: d if d in ['Saturday','Sunday'] else 'Weekday')

# Derived energy and VoW
rho, g, H, eta = 1000, 9.81, 50, 0.9
cfs_to_m3s = 0.0283168
Q = df['turbine_release'] * cfs_to_m3s
df['E_mwh']   = Q * (rho * g * H * eta * 3600) / 1e6
df['revenue'] = df['E_mwh'] * df['LMP']
df['vol_m3']  = Q * 3600
df['VoW']     = df['revenue'] / df['vol_m3']

# Convenience column for scatter
df['deltaT'] = df['temp_GCD'] - df['temp_RM61']

# 4) Example plots

# 4a) Correlation heatmap of daily vars (Matplotlib)
vars_ = ['total_release','LMP','demand','temp_RM61','violations']
corr = daily[vars_].corr()

fig, ax = plt.subplots(figsize=(6,5))
im = ax.imshow(corr.values, cmap='coolwarm', vmin=-1, vmax=1)
ax.set_xticks(range(len(vars_)))
ax.set_xticklabels(vars_, rotation=45, ha='right')
ax.set_yticks(range(len(vars_)))
ax.set_yticklabels(vars_)
# annotate cells
for i in range(len(vars_)):
    for j in range(len(vars_)):
        ax.text(j, i, f"{corr.values[i, j]:.2f}", ha='center', va='center', color='black')
fig.colorbar(im, ax=ax)
ax.set_title("Daily Variable Correlations")
plt.tight_layout()
plt.show()

# 4b) Scatter release vs. temp reduction + regression line (Matplotlib)
fig, ax = plt.subplots(figsize=(6,4))
ax.scatter(df['bp_release'], df['deltaT'], s=10, alpha=0.3, color='C0')
x = df['bp_release'].values
y = df['deltaT'].values
m, b = np.polyfit(x, y, 1)  # linear fit
x_line = np.linspace(x.min(), x.max(), 200)
ax.plot(x_line, m*x_line + b, color='r', lw=2, label=f"Fit: y={m:.4f}x + {b:.2f}")
ax.set_xlabel('Bypass Release (cfs)')
ax.set_ylabel('Temp Drop (°C)')
ax.set_title("Bypass Release vs. Temp Drop")
ax.legend()
plt.tight_layout()
plt.show()

# 4c) Boxplot of VoW by month (Matplotlib)
months_order = ['Jul','Aug','Sep','Oct','Nov']
data_by_month = [df.loc[df.index.month_name().str[:3] == m, 'VoW'].dropna().values
                 for m in months_order]
fig, ax = plt.subplots(figsize=(8,4))
bp = ax.boxplot(data_by_month, labels=months_order, patch_artist=True, showfliers=False)
# color boxes
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
for box, color in zip(bp['boxes'], colors):
    box.set_facecolor(color)
ax.set_ylabel("Value of Water $/m³")
ax.set_title("Hourly VoW by Month")
plt.tight_layout()
plt.show()

# 4d) Violations by Month & DayType (side-by-side boxplots in Matplotlib)
months = ['Jul','Aug','Sep','Oct','Nov']
daytypes = ['Weekday','Saturday','Sunday']
fig, ax = plt.subplots(figsize=(10,4))

width = 0.25
positions = []
data_groups = []
month_centers = np.arange(len(months))

# positions: for each month i, place three boxes at i - width, i, i + width
for i, m in enumerate(months):
    for j, d in enumerate(daytypes):
        mask = (daily['month'] == m) & (daily['daytype'] == d)
        data_groups.append(daily.loc[mask, 'violations'].values)
        positions.append(i + (j - 1) * width)

bp = ax.boxplot(data_groups, positions=positions, widths=width, patch_artist=True, showfliers=False)

colors = ['C0','C1','C2']
for k, box in enumerate(bp['boxes']):
    box.set_facecolor(colors[k % len(colors)])

# x-axis: month centers
ax.set_xticks(month_centers)
ax.set_xticklabels(months)
ax.set_xlim(-0.5, len(months) - 0.5)

# legend
handles = [plt.Line2D([0],[0], color=c, lw=8) for c in colors]
ax.legend(handles, daytypes, title='DayType')
ax.set_ylabel('Violations (count per day)')
ax.set_title("Daily Violations by Month & DayType")
plt.tight_layout()
plt.show()

# 4e) Time-series overview (Matplotlib)
fig, ax1 = plt.subplots(figsize=(12,4))
ax1.plot(daily.index, daily['total_release'], label='Total Release', color='C0')
ax1.set_ylabel('Release (cfs-days)')

ax2 = ax1.twinx()
ax2.plot(daily.index, daily['temp_RM61'], label='RM61 Temp', color='C1')
ax2.set_ylabel('Temp (°C)')

ax1.legend(loc='upper left')
ax2.legend(loc='upper right')
ax1.set_title("Daily Release & RM61 Temperature")
fig.autofmt_xdate()
plt.tight_layout()
plt.show()


