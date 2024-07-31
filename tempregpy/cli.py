from typing import Optional

import typer

from tempregpy import __appname__, __version__
from .functions import *
from .build_pywraplp import *

app = typer.Typer(help="Build and run the TempRegPy model according to a specific config excel file.")

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__appname__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )

) -> None:
    return

@app.command()
def run(
    config: str = typer.Option(
        './ConfigFiles/ConfigTest.xlsx', '--config', '-c', prompt='Specify the path to the config file',
        help='Path to the config file (e.g., ConfigFiles/Config.xlsx)'
    )
):
    """Build simulation files, run optimization, create Results folder and scenario subfolder, export results to .csv files within the config directory"""
    typer.echo(f"Using config file: {config}")
    conf = load_config(config)
    build_and_run(conf)

if __name__ == "__main__":
    app()
