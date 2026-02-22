## TempRegPy
Temperature-constrained hydropower dispatch optimization using Mixed-Integer Linear Programming (MILP).

## Overview
TempRegPy optimizes hydropower release schedules to maximize energy revenue while maintaining downstream water temperatures within ecological limits. It uses selective withdrawal from thermally stratified reservoirs, market-based dispatch, and configurable operational constraints within a MILP framework solved via HiGHS (OR-Tools MathOpt).

## Installation
uv pip install:

```Bash
uv pip install tempregpy
```
Or with pip:


```Bash
pip install tempregpy
```
For development:


```Bash
git clone https://github.com/energy-modelling-hub/TempRegPy.git
cd TempRegPy
uv pip install -e ".[dev]"
```

## Quick Start
Generate a synthetic configuration file:

```Bash
python examples/generate_config.py
```
Run the optimizer:

```Bash
python -m tempregpy run -c examples/config.xlsx
```
See examples/README.md for details on the synthetic test case.

## Features
- MILP-based temperature-constrained hydropower dispatch
- Selective withdrawal from thermally stratified reservoirs
- Multiple bilinear term linearization methods (McCormick, triangles, polygons, sum-of-convex)
- Configurable ramping, cycling, and operating range constraints
- Market-based dispatch with locational marginal prices
- HiGHS solver via OR-Tools MathOpt (open-source)
- Excel-based configuration input
- CLI interface

## Citation
If you use TempRegPy in your research, please cite:

```Code snippet
@article{pavicevic2025tempregpy,
  title={TempRegPy: An Open-Source MILP Framework for Temperature-Constrained Hydropower Dispatch with Application to Glen Canyon Dam},
  author={Pavicevic, Matija and Usis, Maris Andris and Yu, Ao and Henriquez, Walter Antonio and Wilhite, Jerry and Ploussard, Quentin},
  journal={Environmental Modelling \& Software},
  year={2025},
  doi={DOI_PLACEHOLDER}
}
```
## License
MIT License. See LICENSE for details.

# Developers guide (Compile .exe file)
```commandline
python -m venv ./env
./env/scripts/activate
pip install -r requirements2.txt
pyinstaller runwapasim.spec
```
RunWAPASim.exe can be found in the /dist folder