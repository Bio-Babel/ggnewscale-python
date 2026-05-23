"""Internal demo / test datasets used by the tutorial and test suite.

Mirrors R ``datasets::volcano`` / ``datasets::iris`` / ``datasets::mtcars``
and ``ggplot2::mpg``. Bundled here as small CSVs so the tutorial and the
test suite are self-contained without pulling extra dependencies.

This is *not* a public API — the underscore-prefixed module name and the
absence of an ``__init__`` re-export signal that. Use at your own risk;
the data shape can be inspected via the source CSV under
``ggnewscale/resources/`` but breakage between releases is not
contractually guarded.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

__all__ = ["load_volcano", "load_iris", "load_mtcars", "load_mpg"]


_DATA = Path(__file__).resolve().parent / "resources"


def load_volcano() -> np.ndarray:
    """R ``datasets::volcano`` — (87, 61) float matrix of topography heights."""
    return np.loadtxt(_DATA / "volcano.csv", delimiter=",")


def load_iris() -> pd.DataFrame:
    """R ``datasets::iris`` — 150 x 5 (Sepal/Petal Length/Width + Species)."""
    return pd.read_csv(_DATA / "iris.csv")


def load_mtcars() -> pd.DataFrame:
    """R ``datasets::mtcars`` — 32 x 12 with rownames promoted to a ``model`` column."""
    return pd.read_csv(_DATA / "mtcars.csv")


def load_mpg() -> pd.DataFrame:
    """R ``ggplot2::mpg`` — 234 x 11 fuel-economy dataset."""
    return pd.read_csv(_DATA / "mpg.csv")
