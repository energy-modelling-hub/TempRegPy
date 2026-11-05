# TempRegPy Example — Synthetic Single-Dam Network

This directory contains a synthetic example configuration for TempRegPy
with entirely fictional names and physically plausible (but fabricated) data.

## Network Topology
[Source: DamAlpha] --> [Gauge: GaugeDown] | [GridNode1: 50-200 MW demand]



- **1 reservoir** (DamAlpha): 2,000–25,000 CFS turbine capacity, 700–15,000 CFS bypass
- **1 downstream gauge** (GaugeDown): temperature limits 8–18.5°C hourly, 12°C daily average
- **1 grid node** (GridNode1): 50–200 MW demand with diurnal pattern
- **168-hour** (weekly) optimization horizon starting 2024-07-01
- **MILP** formulation with HiGHS solver, 60-second time limit

## Generating the Configuration File

The configuration Excel file is generated programmatically:

```bash
python examples/generate_config.py
```

This creates examples/config.xlsx with all required input parameters.

Running the Example
After generating the config file:

```bash
python -m tempregpy -c examples/config.xlsx
```

The optimizer will:

- Parse the Excel configuration
- Build a temperature-constrained hydropower dispatch model
- Solve the MILP using HiGHS (via OR-Tools MathOpt)
- Log results to the console

## Input Data Summary
| Parameter | Value            |
| :--- |:-----------------|
| Turbine flow | 2,000–25,000 CFS |
| Bypass flow | 700–15,000 CFS   |
| Bypass temperature | 8.0°C            |
| Turbine temperature | 14.0°C           |
| Max hourly gauge temp | 18.5°C           |
| Max daily avg gauge temp | 12.0°C           |
| LMP range | 30–70 $/MWh      |
| Demand range | 50–200 MW        |
| Solver time limit | 60 seconds       |
| Optimality gap | 1%               |

## Notes
- All names are fictional. No real facility data is used.
- The data is physically plausible but entirely fabricated for demonstration.
- This example exercises the full optimization pipeline including temperature constraints, ramping limits, and bypass scheduling.


## River Travel Time (Lag)
Travel time is set **per river link** (rows named like the `river_topology` entries, e.g. `DamAlpha - GaugeDown`):

| Python variable | Name column | Single input | Meaning |
| :--- | :--- | :--- | :--- |
| `lag_hours` | link (`A - B`) | whole hours | Time for water released at A to reach B. Links not listed = 0. |
| `lag_boundary` | – | `Wrap` (default) or `Initial` | What happens for hours where `t - lag` falls before the horizon start. |
| `lag_initial_flow` | link (`A - B`) | CFS (optional) | Flow already in transit at the start (only for `Initial`). Blank = hold the link's first-hour release. |

- `Wrap`: the week is circular, so hour H01 receives water released at the end of the week.
- `Initial`: pre-horizon water is an initial condition. Temperature limits for it use the first hour; releases that would arrive after the horizon end use the last hour's limits.
- Flow released at hour `t` arrives at `t + lag`. Hourly limits and `dT` are evaluated at the arrival hour. Daily limits use the day holding the midpoint of the arrival window.
