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
    typer.echo(f"TempRegPy: config file = {config}")
    typer.echo("Run command not yet fully implemented. See C10b.")


def main():
    app()


if __name__ == "__main__":
    app()
