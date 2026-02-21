"""TempRegPy -- Temperature-constrained hydropower dispatch optimization."""

from tempregpy.model import (
    Model,
    ModelConfig,
    ProductLinearizationConfig,
    ProductLinearizationMethod,
    ParseModelResults,
)
from tempregpy.model.functions import load_config
from tempregpy._version import __version__, version

__appname__ = "TempRegPy"

__all__ = [
    "Model",
    "ModelConfig",
    "ProductLinearizationConfig",
    "ProductLinearizationMethod",
    "ParseModelResults",
    "load_config",
    "__version__",
    "__appname__",
]
