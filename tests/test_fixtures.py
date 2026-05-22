"""Sanity-check that the four R-exported CSV fixtures load with R-known shapes.

R-side ground truth (from `Rscript -e 'dim(datasets::volcano)'` etc.):

- ``volcano``: (87, 61) numeric matrix
- ``iris``:    (150, 5) with one factor column (Species)
- ``mtcars``:  (32, 11) numeric; rownames are car-model strings (we serialise as col)
- ``mpg``:     (234, 11) from ggplot2
"""

from __future__ import annotations

import numpy as np

from ggnewscale._demo_data import load_volcano, load_iris, load_mtcars, load_mpg


def test_volcano_shape_matches_R():
    arr = load_volcano()
    assert arr.shape == (87, 61)
    assert arr.dtype == np.float64
    # Spot-check a known value: volcano[1, 1] in R (1-based) is 100, which is
    # arr[0, 0] in numpy (0-based).
    assert arr[0, 0] == 100.0


def test_iris_shape_and_columns_match_R():
    df = load_iris()
    assert df.shape == (150, 5)
    assert list(df.columns) == [
        "Sepal.Length",
        "Sepal.Width",
        "Petal.Length",
        "Petal.Width",
        "Species",
    ]
    # R: levels(iris$Species) -> "setosa" "versicolor" "virginica" (50 each)
    assert sorted(df["Species"].unique().tolist()) == ["setosa", "versicolor", "virginica"]


def test_mtcars_shape_and_columns_match_R():
    df = load_mtcars()
    # 11 mtcars cols + 1 added "model" col = 12
    assert df.shape == (32, 12)
    assert df.columns[0] == "model"
    assert "mpg" in df.columns and "cyl" in df.columns
    # Spot-check: first row in R is "Mazda RX4", mpg 21.0
    assert df.iloc[0]["model"] == "Mazda RX4"
    assert float(df.iloc[0]["mpg"]) == 21.0


def test_mpg_shape_matches_R():
    df = load_mpg()
    assert df.shape == (234, 11)
    assert "manufacturer" in df.columns
    assert "displ" in df.columns
    assert "hwy" in df.columns
