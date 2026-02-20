#!/usr/bin/env python3
"""Generate a synthetic TempRegPy configuration Excel file.

Creates examples/config.xlsx with entirely fictional river network names
and physically plausible (but fabricated) input data for demonstration
and testing purposes.

Network:
    - 1 reservoir:  DamAlpha   (plant)
    - 1 gauge:      GaugeDown  (downstream gauge)
    - 1 grid node:  GridNode1  (power market node)
    - Topology:     DamAlpha -> GaugeDown
    - 168-hour (7-day) optimization horizon

Usage:
    python examples/generate_config.py
"""

import math
import os
import sys

import openpyxl


def diurnal(hour_of_day, base, amplitude, peak_hour=14):
    """Simple sinusoidal diurnal pattern peaking at *peak_hour*."""
    return base + amplitude * math.sin(math.pi * (hour_of_day - peak_hour + 6) / 12)


def lmp_pattern(hour_of_day):
    """Dual-peak LMP: peaks near hours 8 and 18, trough overnight."""
    morning = 15 * math.exp(-0.5 * ((hour_of_day - 8) / 2.5) ** 2)
    evening = 20 * math.exp(-0.5 * ((hour_of_day - 18) / 2.5) ** 2)
    return 35 + morning + evening


def demand_pattern(hour_of_day):
    """Diurnal demand pattern: 50–200 MW."""
    return diurnal(hour_of_day, base=125, amplitude=75, peak_hour=15)


def main():
    # ------------------------------------------------------------------ #
    # Constants
    # ------------------------------------------------------------------ #
    HOURS = 168  # 7 days × 24 hours
    DAYS = 7
    HOURS_PER_DAY = 24

    PLANT = "DamAlpha"
    GAUGE = "GaugeDown"
    NODE = "GridNode1"
    TOPOLOGY = f"{PLANT} - {GAUGE}"
    PLANT_NODE = f"{PLANT} - {NODE}"

    # Column headers (must match load_config schema exactly)
    COL_A = "Glen Canyon Dam Inputs"  # required parser schema column name
    COL_B = "Python Variable Names"
    COL_C = "Name"
    COL_D = "Single input"
    HOUR_COLS = [f"H{i:02d}" for i in range(1, HOURS + 1)]
    DAILY_COLS = [f"H{i:02d}" for i in range(1, DAYS + 1)]

    ALL_HEADERS = [COL_A, COL_B, COL_C, COL_D] + HOUR_COLS

    # ------------------------------------------------------------------ #
    # Build rows
    # ------------------------------------------------------------------ #
    rows = []

    def add_row(description, pyvar, name=None, single=None, hourly=None, daily=None):
        """Append one row to the sheet data.

        Parameters
        ----------
        description : str   Cell in column A (human-readable label).
        pyvar : str         Cell in column B (Python Variable Names).
        name : str | None   Cell in column C (Name).
        single : value      Cell in column D (Single input).
        hourly : list       168 values for H01..H168.
        daily : list        7 values placed in H01..H07 (rest None).
        """
        row = [description, pyvar, name, single]
        if hourly is not None:
            row.extend(hourly)
        elif daily is not None:
            row.extend(daily)
            row.extend([None] * (HOURS - DAYS))
        else:
            row.extend([None] * HOURS)
        rows.append(row)

    # -- Helper: generate 168-hour constant list
    def const_h(value):
        return [value] * HOURS

    # -- Helper: generate 168-hour diurnal list from a function
    def hourly_from_func(func):
        return [round(func(h % HOURS_PER_DAY), 4) for h in range(HOURS)]

    # -- Helper: generate 7-day constant list
    def const_d(value):
        return [value] * DAYS

    # ================================================================== #
    # SIMULATION OPTIONS / SCALAR PARAMETERS
    # ================================================================== #
    add_row("Model version", "version", single="v0.1.3")
    add_row("Simulation start date", "DateStart", single="2024-07-01")
    add_row("Simulation type (LP or MILP)", "sim_type", single="MILP")
    add_row("Solver time limit (seconds)", "sim_time", single=60)
    add_row("Optimality gap", "opt_gap", single=0.01)
    add_row("Linearization method", "xy_method", single="Sum of Convex")
    add_row("Edge elements for linearization", "edge_elements", single=5)
    add_row("Slack variable cost", "C_slack", single=1000)
    add_row("Results folder", "sim_folder", single="./Results/")
    add_row("Show plots", "plt_show", single=False)

    # Constraint toggles
    add_row("Bypass ramp constraint", "cnstr_bp_ramp", single=True)
    add_row("Turbine ramp constraint", "cnstr_tur_ramp", single=True)
    add_row("Total ramp constraint", "cnstr_tot_ramp", single=True)
    add_row("Gauge ramp constraint", "cnstr_gg_ramp", single=True)
    add_row("Temperature cyclic constraint", "cnstr_temp_t01t24", single=False)
    add_row("Bypass cyclic constraint", "cnstr_bp_t01t24", single=True)
    add_row("Turbine cyclic constraint", "cnstr_tur_t01t24", single=True)
    add_row("Total release cyclic constraint", "cnstr_tot_t01t24", single=True)
    add_row("Gauge cyclic constraint", "cnstr_gg_t01t24", single=True)
    add_row("Operating range constraint", "cnstr_oper_range", single=True)
    add_row("Rough zone constraint", "cnstr_rough_zone", single=False)
    add_row("Pattern repeat mode", "cnstr_pattern_repeat", single="Off")

    # ================================================================== #
    # NETWORK TOPOLOGY (array-valued scalars read via initialize_inputs)
    # ================================================================== #
    add_row("Plant names", "plants", hourly=[PLANT] + [None] * (HOURS - 1))
    add_row("Gauge names", "gauges", hourly=[GAUGE] + [None] * (HOURS - 1))
    add_row("Node names", "nodes", hourly=[NODE] + [None] * (HOURS - 1))
    add_row("River topology", "river_topology",
            hourly=[TOPOLOGY] + [None] * (HOURS - 1))
    add_row("Plant to node mapping", "plant_to_node",
            hourly=[PLANT_NODE] + [None] * (HOURS - 1))
    add_row("Source nodes", "sources",
            hourly=[PLANT] + [None] * (HOURS - 1))
    add_row("Sink nodes", "sinks",
            hourly=[GAUGE] + [None] * (HOURS - 1))

    # ================================================================== #
    # DAILY PARAMETERS (7 values in H01..H07)
    # ================================================================== #
    add_row("Total daily release (AF)", "Q_tot_daily",
            name=PLANT, daily=const_d(240000))
    add_row("Total daily release (AF) - gauge", "Q_tot_daily",
            name=GAUGE, daily=const_d(0))

    add_row("Max daily flow change (CFS)", "Q_max_daily_change",
            name=PLANT, daily=const_d(8000))
    add_row("Max daily flow change - gauge", "Q_max_daily_change",
            name=GAUGE, daily=const_d(0))

    add_row("Water to power conversion (MW/CFS)", "WaterToPowerConversion",
            name=PLANT, daily=const_d(0.01))
    add_row("Water to power conversion - gauge", "WaterToPowerConversion",
            name=GAUGE, daily=const_d(0))

    add_row("Daily gauge temperature max (C)", "T_gauge_daily",
            name=PLANT, daily=const_d(0))
    add_row("Daily gauge temperature max (C)", "T_gauge_daily",
            name=GAUGE, daily=const_d(15.0))

    add_row("Daily temperature delta", "dT_daily",
            name=TOPOLOGY, daily=const_d(-1.5))

    # ================================================================== #
    # PLANT SCALAR PARAMETERS (Name + Single input)
    # ================================================================== #
    scalar_plant_params = {
        "Q_bp_ramp_up_max": ("Bypass ramp up max (CFS/hr)", 2000),
        "Q_bp_ramp_down_max": ("Bypass ramp down max (CFS/hr)", 2000),
        "Q_tur_ramp_up_max": ("Turbine ramp up max (CFS/hr)", 2000),
        "Q_tur_ramp_down_max": ("Turbine ramp down max (CFS/hr)", 2000),
        "Q_tot_ramp_up_max": ("Total ramp up max (CFS/hr)", 2000),
        "Q_tot_ramp_down_max": ("Total ramp down max (CFS/hr)", 2000),
        "Q_gg_ramp_up_max": ("Gauge ramp up max (CFS/hr)", 2000),
        "Q_gg_ramp_down_max": ("Gauge ramp down max (CFS/hr)", 2000),
        "bp_ramp_up_cyc": ("Bypass ramp up cycles per day", 4),
        "bp_ramp_down_cyc": ("Bypass ramp down cycles per day", 4),
        "bp_ramp_tot_cyc": ("Bypass total ramp cycles per day", 8),
    }
    for pyvar, (desc, val) in scalar_plant_params.items():
        add_row(desc, pyvar, name=PLANT, single=val)
        add_row(desc + " - gauge", pyvar, name=GAUGE, single=0)

    # Cost parameters
    cost_params = {
        "C_bp_ramp_up": ("Cost bypass ramp up ($/CFS)", 0.1),
        "C_bp_ramp_down": ("Cost bypass ramp down ($/CFS)", 0.1),
        "C_tur_ramp_up": ("Cost turbine ramp up ($/CFS)", 0.1),
        "C_tur_ramp_down": ("Cost turbine ramp down ($/CFS)", 0.1),
        "C_tot_ramp_up": ("Cost total ramp up ($/CFS)", 0.1),
        "C_tot_ramp_down": ("Cost total ramp down ($/CFS)", 0.1),
        "C_gg_ramp_up": ("Cost gauge ramp up ($/CFS)", 0.1),
        "C_gg_ramp_down": ("Cost gauge ramp down ($/CFS)", 0.1),
    }
    for pyvar, (desc, val) in cost_params.items():
        add_row(desc, pyvar, name=PLANT, single=val)
        add_row(desc + " - gauge", pyvar, name=GAUGE, single=0)

    # ================================================================== #
    # HOURLY PARAMETERS (Name + H01..H168)
    # ================================================================== #

    # --- Flow bounds ---
    add_row("Bypass min flow (CFS)", "Q_bp_min_values",
            name=PLANT, hourly=const_h(0))
    add_row("Bypass min flow - gauge", "Q_bp_min_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Bypass max flow (CFS)", "Q_bp_max_values",
            name=PLANT, hourly=const_h(5000))
    add_row("Bypass max flow - gauge", "Q_bp_max_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Turbine min flow (CFS)", "Q_tur_min_values",
            name=PLANT, hourly=const_h(5000))
    add_row("Turbine min flow - gauge", "Q_tur_min_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Turbine max flow (CFS)", "Q_tur_max_values",
            name=PLANT, hourly=const_h(15000))
    add_row("Turbine max flow - gauge", "Q_tur_max_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Total min flow (CFS)", "Q_tot_min_values",
            name=PLANT, hourly=const_h(5000))
    add_row("Total min flow - gauge", "Q_tot_min_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Total max flow (CFS)", "Q_tot_max_values",
            name=PLANT, hourly=const_h(20000))
    add_row("Total max flow - gauge", "Q_tot_max_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Gauge min flow (CFS)", "Q_gg_min_values",
            name=PLANT, hourly=const_h(5000))
    add_row("Gauge min flow - gauge", "Q_gg_min_values",
            name=GAUGE, hourly=const_h(5000))

    add_row("Gauge max flow (CFS)", "Q_gg_max_values",
            name=PLANT, hourly=const_h(20000))
    add_row("Gauge max flow - gauge", "Q_gg_max_values",
            name=GAUGE, hourly=const_h(20000))

    # --- Temperatures ---
    add_row("Bypass temperature (C)", "T_bp_values",
            name=PLANT, hourly=const_h(8.0))
    add_row("Bypass temperature - gauge", "T_bp_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Turbine temperature (C)", "T_tur_values",
            name=PLANT, hourly=const_h(12.0))
    add_row("Turbine temperature - gauge", "T_tur_values",
            name=GAUGE, hourly=const_h(0))

    # --- Gauge temperature limits ---
    add_row("Gauge hourly min temperature (C)", "T_gauge_hourly_min_values",
            name=GAUGE, hourly=const_h(8.0))

    add_row("Gauge hourly max temperature (C)", "T_gauge_hourly_max_values",
            name=GAUGE, hourly=const_h(16.0))

    # --- Temperature deltas ---
    add_row("Hourly temperature delta (C)", "dT_hourly_values",
            name=TOPOLOGY, hourly=const_h(-1.5))

    # --- Power limits ---
    add_row("Power output min (MW)", "P_tur_min_values",
            name=PLANT, hourly=const_h(0))
    add_row("Power output min - gauge", "P_tur_min_values",
            name=GAUGE, hourly=const_h(0))

    add_row("Power output max (MW)", "P_tur_max_values",
            name=PLANT, hourly=const_h(150))
    add_row("Power output max - gauge", "P_tur_max_values",
            name=GAUGE, hourly=const_h(0))

    # --- Bypass forced commit ---
    add_row("Bypass forced commit status", "bp_forced_commit",
            name=PLANT, hourly=const_h(0))
    add_row("Bypass forced commit - gauge", "bp_forced_commit",
            name=GAUGE, hourly=const_h(0))

    # --- Flow limits between nodes ---
    add_row("Max flow between nodes (CFS)", "Flow_i_j_max",
            name=TOPOLOGY, hourly=const_h(25000))
    add_row("Min flow between nodes (CFS)", "Flow_i_j_min",
            name=TOPOLOGY, hourly=const_h(0))

    # --- Source/sink temperature limits ---
    add_row("Source hourly max temperature (C)", "T_source_hourly_max_values",
            name=TOPOLOGY, hourly=const_h(25))
    add_row("Source hourly min temperature (C)", "T_source_hourly_min_values",
            name=TOPOLOGY, hourly=const_h(0))
    add_row("Sink hourly max temperature (C)", "T_sink_hourly_max_values",
            name=TOPOLOGY, hourly=const_h(30))
    add_row("Sink hourly min temperature (C)", "T_sink_hourly_min_values",
            name=TOPOLOGY, hourly=const_h(0))

    # --- Gauge temperature ramp deltas ---
    add_row("Temperature ramp up delta (C)", "T_ramp_up_delta",
            name=PLANT, single=2.0)
    add_row("Temperature ramp up delta - gauge", "T_ramp_up_delta",
            name=GAUGE, single=2.0)
    add_row("Temperature ramp down delta (C)", "T_ramp_down_delta",
            name=PLANT, single=2.0)
    add_row("Temperature ramp down delta - gauge", "T_ramp_down_delta",
            name=GAUGE, single=2.0)

    # ================================================================== #
    # NODE PARAMETERS
    # ================================================================== #
    add_row("Locational marginal price ($/MWh)", "LMP_values",
            name=NODE, hourly=hourly_from_func(lmp_pattern))

    add_row("Demand (MW)", "Demand_values",
            name=NODE, hourly=hourly_from_func(demand_pattern))

    # ================================================================== #
    # ROUGH ZONE PARAMETERS (disabled but schema requires presence)
    # ================================================================== #
    add_row("Rough zone min flow (CFS)", "Q_rough_zone_min",
            name=PLANT, daily=[0, 4000, 6800, None, None, None, None])
    add_row("Rough zone max flow (CFS)", "Q_rough_zone_max",
            name=PLANT, daily=[2400, 4800, 7200, None, None, None, None])

    # ================================================================== #
    # Write to Excel
    # ================================================================== #
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inputs"

    # Write header row
    ws.append(ALL_HEADERS)

    # Write data rows
    for row in rows:
        ws.append(row)

    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "config.xlsx")

    wb.save(output_path)
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
