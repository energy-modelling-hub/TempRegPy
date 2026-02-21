# TempRegPy Example — Synthetic Single-Dam Network

This directory contains a synthetic example configuration for TempRegPy
with entirely fictional names and physically plausible (but fabricated) data.

## Network Topology
[Source: DamAlpha] --> [Gauge: GaugeDown] | [GridNode1: 50-200 MW demand]



- **1 reservoir** (DamAlpha): 5,000–15,000 CFS turbine capacity, 0–5,000 CFS bypass
- **1 downstream gauge** (GaugeDown): temperature limits 8–16°C hourly, 15°C daily average
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
| Parameter | Value |
| :--- | :--- |
| Turbine flow | 5,000–15,000 CFS |
| Bypass flow | 0–5,000 CFS |
| Bypass temperature | 8.0°C |
| Turbine temperature | 12.0°C |
| Max hourly gauge temp | 16.0°C |
| Max daily avg gauge temp | 15.0°C |
| LMP range | 30–70 $/MWh |
| Demand range | 50–200 MW |
| Solver time limit | 60 seconds |
| Optimality gap | 1% |

## Notes
- All names are fictional. No real facility data is used.
- The data is physically plausible but entirely fabricated for demonstration.
- This example exercises the full optimization pipeline including temperature constraints, ramping limits, and bypass scheduling.

