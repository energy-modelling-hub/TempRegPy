"""TempRegPy -- Temperature-constrained hydropower dispatch optimization."""

from tempregpy.model import (
    Model,
    ModelConfig,
    ProductLinearizationConfig,
    ProductLinearizationMethod,
    parse_model_results,
)
from tempregpy.model.functions import load_config
from tempregpy._version import __version__, version

__appname__ = "TempRegPy"
