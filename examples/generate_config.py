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

import openpyxl


# ---------------------------------------------------------------------------
# Physical / unit constants  (must match tempregpy.model.constants)
# ---------------------------------------------------------------------------
CF_PER_AF = 43560.02
CFS_TO_AFH = 3600 / CF_PER_AF  # ≈ 0.082645 AF per CFS·hour


# ---------------------------------------------------------------------------
# Diurnal pattern helpers
# ---------------------------------------------------------------------------
def lmp_pattern(hour_of_day):
    """Dual-peak LMP: peaks near hours 8 and 18, trough overnight.  30–70 $/MWh."""
    morning = 15 * math.exp(-0.5 * ((hour_of_day - 8) / 2.5) ** 2)
    evening = 20 * math.exp(-0.5 * ((hour_of_day - 18) / 2.5) ** 2)
    return round(35 + morning + evening, 4)


def demand_pattern(hour_of_day):
    """Diurnal demand: 50–200 MW, peaking mid-afternoon."""
    return round(125 + 75 * math.sin(math.pi * (hour_of_day - 15 + 6) / 12), 4)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def main():
    HOURS = 168
    DAYS = 7
    H_PER_D = 24

    PLANT = "DamAlpha"
    GAUGE = "GaugeDown"
    NODE = "GridNode1"
    TOPO = f"{PLANT} - {GAUGE}"
    P2N = f"{PLANT} - {NODE}"

    # ---- Column headers (must match load_config schema) ----
    COL_A = "Glen Canyon Dam Inputs"
    COL_B = "Python Variable Names"
    COL_C = "Name"
    COL_D = "Single input"
    H_COLS = [f"H{i:02d}" for i in range(1, HOURS + 1)]
    ALL_HEADERS = [COL_A, COL_B, COL_C, COL_D] + H_COLS

    # ---- Flow parameters (CFS) ----
    Q_TUR_MIN = 5000
    Q_TUR_MAX = 15000
    Q_BP_MIN = 0
    Q_BP_MAX = 5000
    Q_TOT_MIN = 5000
    Q_TOT_MAX = 20000
    Q_GG_MIN = 5000
    Q_GG_MAX = 20000

    # Target average total release ≈ 10,000 CFS
    # Daily AF = 10000 * CFS_TO_AFH * 24 ≈ 19,835 AF
    Q_AVG_CFS = 10000
    Q_TOT_DAILY_AF = round(Q_AVG_CFS * CFS_TO_AFH * H_PER_D, 0)

    # Max daily operating range (CFS)
    Q_MAX_DAILY_CHANGE = 8000

    # Ramp rates (CFS/hr)
    RAMP_RATE = 2000

    # ---- Temperature parameters (°C) ----
    T_BP = 8.0
    T_TUR = 14.0
    T_GG_MIN = 8.0
    T_GG_MAX = 17.0
    T_GG_DAILY_MAX = 15.0
    DT_HOURLY = -1.5
    DT_DAILY = -1.5

    # ---- Power parameters ----
    P_MIN = 0
    P_MAX = 1500
    W2P = 0.01  # MW per CFS

    # ---- Accumulate rows ----
    rows = []

    def add(desc, pyvar, name=None, single=None, hourly=None, daily=None):
        row = [desc, pyvar, name, single]
        if hourly is not None:
            row.extend(hourly)
        elif daily is not None:
            row.extend(daily)
            row.extend([None] * (HOURS - len(daily)))
        else:
            row.extend([None] * HOURS)
        rows.append(row)

    def ch(v):
        """Constant hourly list."""
        return [v] * HOURS

    def cd(v):
        """Constant daily list (7 values)."""
        return [v] * DAYS

    def hfunc(fn):
        """Hourly list from hour-of-day function."""
        return [fn(h % H_PER_D) for h in range(HOURS)]

    # ==================================================================
    # SCALAR / SIMULATION PARAMETERS
    # ==================================================================
    add("Model version", "version", single="v0.1.3")
    add("Simulation start date", "DateStart", single="2024-07-01")
    add("Simulation type", "sim_type", single="MILP")
    add("Solver time limit (s)", "sim_time", single=60)
    add("Optimality gap", "opt_gap", single=0.01)
    add("Linearization method", "xy_method", single="Sum of Convex")
    add("Edge elements", "edge_elements", single=3)
    add("Slack cost", "C_slack", single=10000)
    add("Results folder", "sim_folder", single="./Results/")
    add("Show plots", "plt_show", single=False)

    # Constraint toggles
    add("Bypass ramp constraint", "cnstr_bp_ramp", single=True)
    add("Turbine ramp constraint", "cnstr_tur_ramp", single=True)
    add("Total ramp constraint", "cnstr_tot_ramp", single=True)
    add("Gauge ramp constraint", "cnstr_gg_ramp", single=False)
    add("Temperature cyclic", "cnstr_temp_t01t24", single=False)
    add("Bypass cyclic", "cnstr_bp_t01t24", single=True)
    add("Turbine cyclic", "cnstr_tur_t01t24", single=False)
    add("Total cyclic", "cnstr_tot_t01t24", single=False)
    add("Gauge cyclic", "cnstr_gg_t01t24", single=False)
    add("Operating range", "cnstr_oper_range", single=True)
    add("Rough zone", "cnstr_rough_zone", single=False)
    add("Pattern repeat", "cnstr_pattern_repeat", single="Off")

    # ==================================================================
    # NETWORK TOPOLOGY
    # ==================================================================
    add("Plant names", "plants", hourly=[PLANT] + [None] * (HOURS - 1))
    add("Gauge names", "gauges", hourly=[GAUGE] + [None] * (HOURS - 1))
    add("Node names", "nodes", hourly=[NODE] + [None] * (HOURS - 1))
    add("River topology", "river_topology", hourly=[TOPO] + [None] * (HOURS - 1))
    add("Plant to node", "plant_to_node", hourly=[P2N] + [None] * (HOURS - 1))
    add("Sources", "sources", hourly=[PLANT] + [None] * (HOURS - 1))
    add("Sinks", "sinks", hourly=[GAUGE] + [None] * (HOURS - 1))

    # ==================================================================
    # DAILY PARAMETERS  (7 values in H01..H07, mapped to D01..D07)
    # ==================================================================
    add("Total daily release (AF)", "Q_tot_daily", name=PLANT, daily=cd(Q_TOT_DAILY_AF))
    add("Total daily release - gauge", "Q_tot_daily", name=GAUGE, daily=cd(0))

    add("Max daily change (CFS)", "Q_max_daily_change", name=PLANT, daily=cd(Q_MAX_DAILY_CHANGE))
    add("Max daily change - gauge", "Q_max_daily_change", name=GAUGE, daily=cd(0))

    add("Water-to-power (MW/CFS)", "WaterToPowerConversion", name=PLANT, daily=cd(W2P))
    add("Water-to-power - gauge", "WaterToPowerConversion", name=GAUGE, daily=cd(0))

    add("Daily gauge temp max", "T_gauge_daily", name=PLANT, daily=cd(0))
    add("Daily gauge temp max", "T_gauge_daily", name=GAUGE, daily=cd(T_GG_DAILY_MAX))

    add("Daily temp delta", "dT_daily", name=TOPO, daily=cd(DT_DAILY))

    # ==================================================================
    # PLANT SCALAR PARAMETERS  (Name + Single input)
    # ==================================================================
    plant_scalars = {
        "Q_bp_ramp_up_max": RAMP_RATE,
        "Q_bp_ramp_down_max": RAMP_RATE,
        "Q_tur_ramp_up_max": RAMP_RATE,
        "Q_tur_ramp_down_max": RAMP_RATE,
        "Q_tot_ramp_up_max": RAMP_RATE,
        "Q_tot_ramp_down_max": RAMP_RATE,
        "Q_gg_ramp_up_max": RAMP_RATE,
        "Q_gg_ramp_down_max": RAMP_RATE,
        "bp_ramp_up_cyc": 4,
        "bp_ramp_down_cyc": 4,
        "bp_ramp_tot_cyc": 4,
    }
    for pyvar, val in plant_scalars.items():
        add(pyvar, pyvar, name=PLANT, single=val)
        add(pyvar + " - gauge", pyvar, name=GAUGE, single=0)

    # Cost scalars
    cost_scalars = {
        "C_bp_ramp_up": 0.1,
        "C_bp_ramp_down": 0.1,
        "C_tur_ramp_up": 0.1,
        "C_tur_ramp_down": 0.1,
        "C_tot_ramp_up": 0.0,
        "C_tot_ramp_down": 0.0,
        "C_gg_ramp_up": 0.0,
        "C_gg_ramp_down": 0.0,
    }
    for pyvar, val in cost_scalars.items():
        add(pyvar, pyvar, name=PLANT, single=val)
        add(pyvar + " - gauge", pyvar, name=GAUGE, single=0)

    # ==================================================================
    # HOURLY PARAMETERS  (Name + H01..H168)
    # ==================================================================
    # Bypass
    add("Bypass min (CFS)", "Q_bp_min_values", name=PLANT, hourly=ch(Q_BP_MIN))
    add("Bypass min - gauge", "Q_bp_min_values", name=GAUGE, hourly=ch(0))
    add("Bypass max (CFS)", "Q_bp_max_values", name=PLANT, hourly=ch(Q_BP_MAX))
    add("Bypass max - gauge", "Q_bp_max_values", name=GAUGE, hourly=ch(0))

    # Turbine
    add("Turbine min (CFS)", "Q_tur_min_values", name=PLANT, hourly=ch(Q_TUR_MIN))
    add("Turbine min - gauge", "Q_tur_min_values", name=GAUGE, hourly=ch(0))
    add("Turbine max (CFS)", "Q_tur_max_values", name=PLANT, hourly=ch(Q_TUR_MAX))
    add("Turbine max - gauge", "Q_tur_max_values", name=GAUGE, hourly=ch(0))

    # Total
    add("Total min (CFS)", "Q_tot_min_values", name=PLANT, hourly=ch(Q_TOT_MIN))
    add("Total min - gauge", "Q_tot_min_values", name=GAUGE, hourly=ch(0))
    add("Total max (CFS)", "Q_tot_max_values", name=PLANT, hourly=ch(Q_TOT_MAX))
    add("Total max - gauge", "Q_tot_max_values", name=GAUGE, hourly=ch(0))

    # Gauge
    add("Gauge min (CFS)", "Q_gg_min_values", name=PLANT, hourly=ch(Q_GG_MIN))
    add("Gauge min - gauge", "Q_gg_min_values", name=GAUGE, hourly=ch(Q_GG_MIN))
    add("Gauge max (CFS)", "Q_gg_max_values", name=PLANT, hourly=ch(Q_GG_MAX))
    add("Gauge max - gauge", "Q_gg_max_values", name=GAUGE, hourly=ch(Q_GG_MAX))

    # Temperatures
    add("Bypass temp (C)", "T_bp_values", name=PLANT, hourly=ch(T_BP))
    add("Bypass temp - gauge", "T_bp_values", name=GAUGE, hourly=ch(0))
    add("Turbine temp (C)", "T_tur_values", name=PLANT, hourly=ch(T_TUR))
    add("Turbine temp - gauge", "T_tur_values", name=GAUGE, hourly=ch(0))

    # Gauge temperature limits (only for gauge node)
    add("Gauge hourly min temp (C)", "T_gauge_hourly_min_values",
        name=GAUGE, hourly=ch(T_GG_MIN))
    add("Gauge hourly max temp (C)", "T_gauge_hourly_max_values",
        name=GAUGE, hourly=ch(T_GG_MAX))

    # Temperature deltas
    add("Hourly temp delta (C)", "dT_hourly_values", name=TOPO, hourly=ch(DT_HOURLY))

    # Power limits
    add("Power min (MW)", "P_tur_min_values", name=PLANT, hourly=ch(P_MIN))
    add("Power min - gauge", "P_tur_min_values", name=GAUGE, hourly=ch(0))
    add("Power max (MW)", "P_tur_max_values", name=PLANT, hourly=ch(P_MAX))
    add("Power max - gauge", "P_tur_max_values", name=GAUGE, hourly=ch(0))

    # Bypass forced commit
    add("Bypass forced commit", "bp_forced_commit", name=PLANT, hourly=ch(0))
    add("Bypass forced commit - gauge", "bp_forced_commit", name=GAUGE, hourly=ch(0))

    # Flow limits between nodes
    add("Max flow i-j (CFS)", "Flow_i_j_max", name=TOPO, hourly=ch(25000))
    add("Min flow i-j (CFS)", "Flow_i_j_min", name=TOPO, hourly=ch(0))

    # Source/sink temperature limits
    add("Source max temp (C)", "T_source_hourly_max_values", name=TOPO, hourly=ch(25))
    add("Source min temp (C)", "T_source_hourly_min_values", name=TOPO, hourly=ch(0))
    add("Sink max temp (C)", "T_sink_hourly_max_values", name=TOPO, hourly=ch(30))
    add("Sink min temp (C)", "T_sink_hourly_min_values", name=TOPO, hourly=ch(0))

    # Temperature ramp deltas
    add("Temp ramp up delta", "T_ramp_up_delta", name=PLANT, single=4.0)
    add("Temp ramp up delta - gauge", "T_ramp_up_delta", name=GAUGE, single=4.0)
    add("Temp ramp down delta", "T_ramp_down_delta", name=PLANT, single=4.0)
    add("Temp ramp down delta - gauge", "T_ramp_down_delta", name=GAUGE, single=4.0)

    # ==================================================================
    # NODE PARAMETERS
    # ==================================================================
    add("LMP ($/MWh)", "LMP_values", name=NODE, hourly=hfunc(lmp_pattern))
    add("Demand (MW)", "Demand_values", name=NODE, hourly=hfunc(demand_pattern))

    # ==================================================================
    # ROUGH ZONES (disabled, but schema requires rows)
    # ==================================================================
    add("Rough zone min (CFS)", "Q_rough_zone_min", name=PLANT,
        daily=[0, 4000, None, None, None, None, None])
    add("Rough zone max (CFS)", "Q_rough_zone_max", name=PLANT,
        daily=[2400, 4800, None, None, None, None, None])

    # ==================================================================
    # WRITE EXCEL
    # ==================================================================
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inputs"
    ws.append(ALL_HEADERS)
    for row in rows:
        ws.append(row)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.xlsx")
    wb.save(out)
    print(f"Generated {out}")


if __name__ == "__main__":
    main()
