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

    logger.info("Optimization complete.")
    logger.info(f"Finished at {datetime.datetime.now()}")


def main():
    app()


if __name__ == "__main__":
    app()
