"""Minimal smoke tests for TempRegPy."""

import subprocess
import sys


def test_import():
    """Package imports without error."""
    import tempregpy

    assert hasattr(tempregpy, "__version__")
    assert hasattr(tempregpy, "Model")
    assert hasattr(tempregpy, "ModelConfig")
    assert hasattr(tempregpy, "load_config")
    assert hasattr(tempregpy, "__appname__")
    assert hasattr(tempregpy, "ParseModelResults")
    assert not hasattr(tempregpy, "parse_model_results")


def test_version_string():
    """Version is a non-empty string."""
    from tempregpy import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_cli_help():
    """CLI --help exits cleanly.

    Note: typer 0.21.1 promotes a single @app.command() to the root,
    so the invocation is ``python -m tempregpy --help`` (no subcommand).
    """
    result = subprocess.run(
        [sys.executable, "-m", "tempregpy", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "config" in result.stdout.lower()


def test_no_wapa_in_public_api():
    """wapa module symbols are not exposed in the public API."""
    import tempregpy

    assert not hasattr(tempregpy, "export_results_to_excel")
    assert not hasattr(tempregpy, "load_inputs_from_excel")
    assert not hasattr(tempregpy, "copy_file_to_destination")
    assert not hasattr(tempregpy, "logger")
    assert not hasattr(tempregpy, "setup_logging")
