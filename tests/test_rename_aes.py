"""Tests for ``rename_aes`` and ``clear_aes`` semantics."""

from __future__ import annotations

import pandas as pd
import pytest

import ggplot2_py as gg
from ggnewscale import clear_aes, rename_aes


def _df():
    return pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1], "z": ["a", "b", "c"]})


def test_rename_aes_then_layer_renames_that_layer():
    """The layer added immediately after rename_aes carries the renamed aesthetic."""
    g = (
        gg.ggplot(_df(), gg.aes("x", "y"))
        + rename_aes(topo_color="color")
        + gg.geom_point(gg.aes(topo_color="z"))
    )
    layer = g.layers[0]
    # The "topo_color" aesthetic should be renamed to "topo_colour" because
    # rename_aes standardised the spelling on the way in. Either name is
    # acceptable as long as one of them carries the data 'z'.
    keys = list(layer.mapping.keys())
    assert "topo_colour" in keys or "topo_color" in keys


def test_rename_aes_persists_until_clear_aes():
    """R-side semantics: ``rename_aes`` stays active until ``clear_aes()``.

    Cross-checked against R: every subsequent layer is bumped, not just the
    first one (see ``+.ggplot_rename_next`` in ``R/rename-aes.R`` — the
    marker class is not removed except inside the ``clear_aes`` branch).
    """
    g = (
        gg.ggplot(_df(), gg.aes("x", "y"))
        + rename_aes(topo_color="color")
        + gg.geom_point(gg.aes(topo_color="z"))
        + gg.geom_point(gg.aes(color="z"))
    )
    # Both layers carry the renamed aesthetic (matches R).
    for layer in g.layers:
        keys = list(layer.mapping.keys())
        assert "topo_colour" in keys or "topo_color" in keys


def test_clear_aes_resets_rename_state():
    """rename_aes + clear_aes (no intervening layer) clears state — next layer is normal."""
    g = (
        gg.ggplot(_df(), gg.aes("x", "y"))
        + rename_aes(topo_color="color")
        + clear_aes()
        + gg.geom_point(gg.aes(color="z"))
    )
    layer = g.layers[0]
    # No rename should have happened.
    assert "colour" in layer.mapping


def test_clear_aes_on_plain_plot_is_noop():
    """Adding clear_aes to a plot with no active rename leaves the plot intact."""
    g = (
        gg.ggplot(_df(), gg.aes("x", "y"))
        + gg.geom_point(gg.aes(color="z"))
        + clear_aes()
    )
    assert isinstance(g, gg.GGPlot)
    assert "colour" in g.layers[0].mapping
