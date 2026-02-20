import numpy as np
from scipy.spatial import ConvexHull

from ..logging_config import *
from ortools.math_opt.python import mathopt

from tempregpy.model.functions import (
    HullComputation,
    gen_hulls,
    gauge_hulls,
    gauge_hulls_time,
)


def do_mathopt_simple_product_linearization(
    model: mathopt.Model,
    X_var: mathopt.Variable,
    Y_var: mathopt.Variable,
    Z_var: mathopt.Variable,
):
    logger.debug(
        "Performing simple product linearization for variables: "
        f"{X_var.name}, {Y_var.name}, {Z_var.name}"
    )

    hull = gen_hulls(
        (X_var.lower_bound, X_var.upper_bound),
        (Y_var.lower_bound, Y_var.upper_bound),
    )

    constraints = []
    for j in range(0, 4):
        if hull.inequality_signs[j] == '<=':
            constraints.append(
                model.add_linear_constraint(
                    hull.plane_equations[j][0] * X_var
                    + hull.plane_equations[j][1] * Y_var
                    + hull.plane_equations[j][2] * Z_var
                    <= hull.plane_equations[j][3]
                )
            )
        elif hull.inequality_signs[j] == '>=':
            constraints.append(
                model.add_linear_constraint(
                    hull.plane_equations[j][0] * X_var
                    + hull.plane_equations[j][1] * Y_var
                    + hull.plane_equations[j][2] * Z_var
                    >= hull.plane_equations[j][3]
                )
            )

    return constraints
