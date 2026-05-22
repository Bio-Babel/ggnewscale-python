"""Test-side dataset loaders for the four R / ggplot2 datasets used by ggnewscale.

These are NOT part of the runtime ggnewscale package. They live in the test
suite and load CSVs that were exported by
``port_reports/ggnewscale/data_exports/export_fixtures.R``.

See ``port_reports/ggnewscale/03_data_asset_strategy.md``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

__all__ = ["FIXTURES_DIR", "load_volcano", "load_iris", "load_mtcars", "load_mpg"]

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def load_volcano() -> np.ndarray:
    """Load R's ``datasets::volcano`` as a (87, 61) float matrix.

    Returns
    -------
    np.ndarray
        Two-dimensional array of topography heights.
    """
    return np.loadtxt(FIXTURES_DIR / "volcano.csv", delimiter=",")


def load_iris() -> pd.DataFrame:
    """Load R's ``datasets::iris`` as a 150x5 DataFrame.

    Returns
    -------
    pandas.DataFrame
        Columns: ``Sepal.Length``, ``Sepal.Width``, ``Petal.Length``,
        ``Petal.Width``, ``Species``.
    """
    return pd.read_csv(FIXTURES_DIR / "iris.csv")


def load_mtcars() -> pd.DataFrame:
    """Load R's ``datasets::mtcars`` as a 32x12 DataFrame (rownames -> ``model`` col).

    Returns
    -------
    pandas.DataFrame
        Columns: ``model`` (car name), then the 11 mtcars numeric columns.
    """
    return pd.read_csv(FIXTURES_DIR / "mtcars.csv")


def load_mpg() -> pd.DataFrame:
    """Load ggplot2's ``mpg`` dataset as a 234x11 DataFrame.

    Returns
    -------
    pandas.DataFrame
        Columns: ``manufacturer``, ``model``, ``displ``, ``year``, ``cyl``,
        ``trans``, ``drv``, ``cty``, ``hwy``, ``fl``, ``class``.
    """
    return pd.read_csv(FIXTURES_DIR / "mpg.csv")
