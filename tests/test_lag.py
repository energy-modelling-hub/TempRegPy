"""Tests for per-link river travel time (lag_hours)."""

import importlib.util
import pathlib

import numpy as np
import openpyxl
import pytest
from ortools.math_opt.python import mathopt

from tempregpy.model import Model, ModelConfig
from tempregpy.model.functions import (
    advanced_hour,
    lagged_hour,
    link_lag_hours,
    load_config,
    normalize_lag_boundary,
)
from tempregpy.model.product_linearization import ProductLinearizationConfig, ProductLinearizationMethod

N = 168


# ---------------------------------------------------------------- helpers
def test_lagged_hour_inside_horizon():
    assert lagged_hour(10, 3, N, "Wrap") == (7, False)
    assert lagged_hour(10, 3, N, "Initial") == (7, False)


def test_lagged_hour_wrap():
    assert lagged_hour(0, 3, N, "Wrap") == (165, False)


def test_lagged_hour_initial_condition():
    assert lagged_hour(0, 3, N, "Initial") == (0, True)
    assert lagged_hour(2, 3, N, "Initial") == (0, True)
    assert lagged_hour(3, 3, N, "Initial") == (0, False)


def test_advanced_hour():
    assert advanced_hour(10, 3, N, "Wrap") == 13
    assert advanced_hour(166, 3, N, "Wrap") == 1
    assert advanced_hour(166, 3, N, "Initial") == N - 1


def test_zero_lag_is_identity():
    for b in ("Wrap", "Initial"):
        assert lagged_hour(5, 0, N, b) == (5, False)
        assert advanced_hour(5, 0, N, b) == 5


def test_normalize_boundary():
    assert normalize_lag_boundary(None) == "Wrap"
    assert normalize_lag_boundary(float("nan")) == "Wrap"
    assert normalize_lag_boundary(" initial ") == "Initial"
    with pytest.raises(ValueError):
        normalize_lag_boundary("bogus")


def test_link_lag_hours_scalar_and_missing():
    inputs = {"river_nodes": ["A", "B"]}
    assert link_lag_hours(inputs)[("A", "B")] == 0
    inputs["lag_hours"] = 4
    assert link_lag_hours(inputs)[("A", "B")] == 4


# ------------------------------------------------------- config + model
def _make_config(tmp_path, lag, boundary=None, initial_flow=None):
    spec = importlib.util.spec_from_file_location(
        "generate_config", pathlib.Path(__file__).parent.parent / "examples" / "generate_config.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    path = tmp_path / "config.xlsx"
    mod.main(out=str(path))

    wb = openpyxl.load_workbook(path)
    ws = wb["Inputs"]
    for row in ws.iter_rows(min_row=2):
        var = row[1].value
        if var == "lag_hours":
            row[3].value = lag
        elif var == "lag_boundary" and boundary is not None:
            row[3].value = boundary
        elif var == "lag_initial_flow" and initial_flow is not None:
            row[3].value = initial_flow
    wb.save(path)
    return str(path)


def test_load_config_reads_lag_inputs(tmp_path):
    inputs = load_config(_make_config(tmp_path, lag=5, boundary="Initial", initial_flow=9000))
    assert inputs["lag_boundary"] == "Initial"
    assert link_lag_hours(inputs)[("DamAlpha", "GaugeDown")] == 5
    assert link_lag_hours(inputs)[("GaugeDown", "DamAlpha")] == 0
    assert not np.isnan(inputs["lag_initial_flow"].iloc[0, 0])


def test_negative_lag_rejected(tmp_path):
    with pytest.raises(SystemExit):
        load_config(_make_config(tmp_path, lag=-1))


@pytest.mark.parametrize("boundary,initial_flow", [("Wrap", None), ("Initial", None), ("Initial", 9000)])
def test_model_builds_and_solves_with_lag(tmp_path, boundary, initial_flow):
    inputs = load_config(_make_config(tmp_path, lag=3, boundary=boundary, initial_flow=initial_flow))
    inputs["sim_time"] = 20
    model = Model(ModelConfig(
        name="lag-test",
        solver_type=mathopt.SolverType.HIGHS,
        product_linearization=ProductLinearizationConfig(method=ProductLinearizationMethod.SUM_OF_CONVEX, N=3),
    ))
    model.populate_from_inputs(inputs)
    result = model.solve(time_limit=20, optimality_gap=0.05)
    assert result.termination.reason in (
        mathopt.TerminationReason.OPTIMAL,
        mathopt.TerminationReason.FEASIBLE,
    )


@pytest.mark.parametrize("boundary,initial_flow", [("Wrap", None), ("Initial", None), ("Initial", 9000)])
def test_inflow_is_release_shifted_by_lag(tmp_path, boundary, initial_flow):
    """Gauge inflow at hour t equals the plant->gauge release at t - lag (wrap / initial condition)."""
    lag = 3
    inputs = load_config(_make_config(tmp_path, lag=lag, boundary=boundary, initial_flow=initial_flow))
    model = Model(ModelConfig(
        name="lag-shift",
        solver_type=mathopt.SolverType.HIGHS,
        product_linearization=ProductLinearizationConfig(method=ProductLinearizationMethod.SUM_OF_CONVEX, N=3),
    ))
    model.populate_from_inputs(inputs)
    result = model.solve(time_limit=20, optimality_gap=0.05)

    nodes = list(inputs["river_nodes"])
    p, g = nodes.index("DamAlpha"), nodes.index("GaugeDown")
    q_in = result.variable_values(model.variables["q_in_flow"][g])
    release = result.variable_values(model.variables["q_flow"][p][g])
    for t in range(N):
        src = t - lag
        if src >= 0:
            expected = release[src]
        elif boundary == "Wrap":
            expected = release[src % N]
        elif initial_flow is not None:
            expected = initial_flow * 3600 / 43560.02
        else:
            expected = release[0]
        assert q_in[t] == pytest.approx(expected, abs=1e-4), f"hour {t}"
