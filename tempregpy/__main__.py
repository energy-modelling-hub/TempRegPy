"""TempRegPy CLI entry point."""

import typer

app = typer.Typer(
    help="TempRegPy -- Temperature-constrained hydropower dispatch optimization.",
)


@app.command()
def run(
    config: str = typer.Option(
        ...,
        "-c",
        "--config",
        help="Path to the configuration Excel file (.xlsm or .xlsx)",
    ),
):
    """Run the optimization model from a configuration Excel file."""
    import os
    import sys
    import datetime

    from tempregpy.logging_config import logger
    from tempregpy.model.functions import load_config
    from tempregpy.model import Model, ModelConfig
    from tempregpy.model.product_linearization import (
        ProductLinearizationConfig,
        ProductLinearizationMethod,
    )
    from tempregpy.model.results import parse_model_results
    from ortools.math_opt.python import mathopt

    timestamp = datetime.datetime.now()
    logger.info(f"TempRegPy run started at {timestamp}")
    logger.info(f"Configuration file: {os.path.abspath(config)}")

    if not os.path.exists(config):
        logger.error(f"Configuration file not found: {config}")
        raise typer.Exit(code=1)

    try:
        inputs = load_config(config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise typer.Exit(code=1)

    edge_elements = inputs.get('edge_elements', 10)
    if not isinstance(edge_elements, int):
        edge_elements = 10

    model_config = ModelConfig(
        name="Bypass Optimization",
        solver_type=mathopt.SolverType.HIGHS,
        product_linearization=ProductLinearizationConfig(
            method=ProductLinearizationMethod.SUM_OF_CONVEX,
            N=edge_elements,
        ),
    )

    model = Model(model_config)
    logger.info("Preparing model with inputs...")

    try:
        model.populate_from_inputs(inputs)
    except Exception as e:
        logger.error(f"Failed to populate model: {e}")
        raise typer.Exit(code=1)

    try:
        time_limit = inputs.get('sim_time', 60)
        opt_gap = inputs.get('opt_gap', 0.01)
        solve_result = model.solve(
            time_limit=time_limit,
            optimality_gap=opt_gap,
        )
    except KeyboardInterrupt:
        logger.error("Model solving interrupted by user.")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Solver failed: {e}")
        raise typer.Exit(code=1)

    try:
        results = parse_model_results(inputs, solve_result, model.variables)
    except Exception as e:
        logger.error(f"Failed to parse results: {e}")
        raise typer.Exit(code=1)

    # Save results to CSV files
    results_dir = inputs.get('sim_folder', './Results/')
    if not isinstance(results_dir, str):
        results_dir = './Results/'
    os.makedirs(results_dir, exist_ok=True)

    csv_exports = {
        'q_bp': 'bypass_release_cfs.csv',
        'q_tur': 'turbine_release_cfs.csv',
        'q_tot': 'total_release_cfs.csv',
        'p_tur': 'power_output_mw.csv',
        'T_gg': 'gauge_temperature_c.csv',
        'T_plant': 'plant_temperature_c.csv',
        'q_gg': 'gauge_flow_cfs.csv',
    }

    for key, filename in csv_exports.items():
        if key in results and hasattr(results[key], 'to_csv'):
            filepath = os.path.join(results_dir, filename)
            results[key].to_csv(filepath)
            logger.info(f"Saved {filepath}")

    obj_path = os.path.join(results_dir, 'objective_value.txt')
    with open(obj_path, 'w') as f:
        f.write(f"Objective value: {results.get('Obj func', 'N/A')}\n")
    logger.info(f"Saved {obj_path}")

    logger.info(f"Results saved to {os.path.abspath(results_dir)}")
    logger.info("Optimization complete.")
    logger.info(f"Finished at {datetime.datetime.now()}")


def main():
    app()


if __name__ == "__main__":
    app()
