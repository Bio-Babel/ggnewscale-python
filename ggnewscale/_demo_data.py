"""Internal demo / test datasets used by the tutorial and test suite.

Mirrors R ``datasets::volcano`` / ``datasets::iris`` / ``datasets::mtcars``
and ``ggplot2::mpg``. Bundled here as small CSVs so the tutorial and the
test suite are self-contained without pulling extra dependencies.

This is *not* a public API — the underscore-prefixed module name and the
absence of an ``__init__`` re-export signal that. Use at your own risk;
the data shape can be inspected via the source CSV under
:data:`ggnewscale.resources.data` but breakage between releases is not
contractually guarded.
"""

from __future__ import annotations

from importlib.resources import files

import numpy as np
import pandas as pd

__all__ = ["load_volcano", "load_iris", "load_mtcars", "load_mpg"]


_DATA = files("ggnewscale.resources.data")


def load_volcano() -> np.ndarray:
    """R ``datasets::volcano`` — (87, 61) float matrix of topography heights."""
    with _DATA.joinpath("volcano.csv").open("rb") as f:
        return np.loadtxt(f, delimiter=",")


def load_iris() -> pd.DataFrame:
    """R ``datasets::iris`` — 150 x 5 (Sepal/Petal Length/Width + Species)."""
    with _DATA.joinpath("iris.csv").open("rb") as f:
        return pd.read_csv(f)


def load_mtcars() -> pd.DataFrame:
    """R ``datasets::mtcars`` — 32 x 12 with rownames promoted to a ``model`` column."""
    with _DATA.joinpath("mtcars.csv").open("rb") as f:
        return pd.read_csv(f)


def load_mpg() -> pd.DataFrame:
    """R ``ggplot2::mpg`` — 234 x 11 fuel-economy dataset."""
    with _DATA.joinpath("mpg.csv").open("rb") as f:
        return pd.read_csv(f)
