"""Unit tests for the bump_aes_* helpers (``ggnewscale._bump``)."""

from __future__ import annotations

import pandas as pd
import pytest

import ggplot2_py as gg
from ggnewscale._bump import (
    bump_aes_guides,
    bump_aes_labels,
    bump_aes_layer,
    bump_aes_layers,
    bump_aes_scale,
    bump_aes_scales,
)
from ggnewscale._protect import is_protected


def _df():
    return pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1], "z": ["a", "b", "c"]})


# --------------------------- bump_aes_layer ---------------------------------


def test_bump_aes_layer_renames_explicit_mapping():
    layer = gg.geom_point(gg.aes(color="z"))
    bumped = bump_aes_layer(layer, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert "colour_ggnewscale_1" in bumped.mapping
    assert "colour" not in bumped.mapping


def test_bump_aes_layer_returns_clone_not_original_for_renamed():
    layer = gg.geom_point(gg.aes(color="z"))
    bumped = bump_aes_layer(layer, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert bumped is not layer
    # Original layer's mapping is intact.
    assert "colour" in layer.mapping


def test_bump_aes_layer_marks_protected():
    layer = gg.geom_point(gg.aes(color="z"))
    bumped = bump_aes_layer(layer, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert is_protected(bumped, "colour")


def test_bump_aes_layer_skips_already_protected():
    """A second call must be a no-op (idempotence)."""
    layer = gg.geom_point(gg.aes(color="z"))
    bumped = bump_aes_layer(layer, original_aes="colour", new_aes="colour_ggnewscale_1")
    bumped2 = bump_aes_layer(bumped, original_aes="colour", new_aes="colour_ggnewscale_2")
    assert bumped2 is bumped
    assert "colour_ggnewscale_1" in bumped2.mapping
    assert "colour_ggnewscale_2" not in bumped2.mapping


def test_bump_aes_layer_no_change_when_layer_doesnt_use_aesthetic():
    """A geom that doesn't use the aesthetic in mapping/default_aes/stat is untouched."""
    # geom_blank has no fill default.
    layer = gg.geom_blank()
    bumped = bump_aes_layer(layer, original_aes="fill", new_aes="fill_ggnewscale_1")
    # Returns a clone; mapping is still empty / no fill renamed.
    assert "fill_ggnewscale_1" not in (bumped.mapping or {})


def test_bump_aes_layer_installs_stat_handle_na():
    """R parity: ``bump_aes_layer`` must install ``handle_na`` on the new stat.

    R reference: ``R/bump-aes-layers.R:64-67`` defines a wrap that renames
    ``new_aes`` -> ``original_aes`` on data columns before delegating to
    the parent stat's ``handle_na``. The new stat must carry this method
    even though ggplot2_py's base Stat does not currently call it — for
    parity and so the rename flows correctly if ggplot2_py adds the call.
    """
    layer = gg.geom_point(gg.aes(color="z"))
    bumped = bump_aes_layer(layer, original_aes="colour", new_aes="colour_ggnewscale_1")

    # The new stat carries handle_na as a callable.
    assert hasattr(bumped.stat, "handle_na")
    assert callable(bumped.stat.handle_na)
    # And is_new is set so subsequent bumps don't stack wraps.
    assert bumped.stat.is_new is True


def test_bumped_stat_handle_na_renames_columns_before_delegating():
    """Functional check: stat.handle_na receives renamed data."""
    import pandas as pd

    layer = gg.geom_point(gg.aes(color="z"))
    bumped = bump_aes_layer(layer, original_aes="colour", new_aes="colour_ggnewscale_1")

    df = pd.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0], "colour_ggnewscale_1": ["a", "b"]})
    # The wrap renames columns then delegates to parent.handle_na (which may
    # or may not exist on ggplot2_py's Stat — the wrap is defensive).
    out = bumped.stat.handle_na(df, {})
    # Parent has no handle_na in current ggplot2_py; the wrap returns the
    # renamed data as-is. Verify the rename did happen.
    assert "colour" in out.columns
    assert "colour_ggnewscale_1" not in out.columns


def test_bump_aes_layers_applies_to_each():
    layers = [
        gg.geom_point(gg.aes(color="z")),
        gg.geom_point(gg.aes(color="z")),
    ]
    out = bump_aes_layers(layers, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert len(out) == 2
    for l in out:
        assert "colour_ggnewscale_1" in l.mapping


# --------------------------- bump_aes_scale ---------------------------------


def test_bump_aes_scale_renames_aesthetics_list():
    scale = gg.scale_color_continuous()
    assert scale.aesthetics == ["colour"]
    bumped = bump_aes_scale(scale, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert "colour_ggnewscale_1" in bumped.aesthetics
    assert "colour" not in bumped.aesthetics


def test_bump_aes_scale_marks_protected():
    scale = gg.scale_color_continuous()
    bumped = bump_aes_scale(scale, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert is_protected(bumped, "colour")


def test_bump_aes_scale_idempotent():
    scale = gg.scale_color_continuous()
    bumped = bump_aes_scale(scale, original_aes="colour", new_aes="colour_ggnewscale_1")
    bumped2 = bump_aes_scale(bumped, original_aes="colour", new_aes="colour_ggnewscale_99")
    assert bumped2 is bumped
    assert "colour_ggnewscale_1" in bumped.aesthetics


def test_bump_aes_scale_none_returns_none():
    assert bump_aes_scale(None, "colour", "colour_ggnewscale_1") is None


def test_bump_aes_scales_applies_to_each():
    scales = [gg.scale_color_continuous(), gg.scale_fill_continuous()]
    out = bump_aes_scales(scales, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert "colour_ggnewscale_1" in out[0].aesthetics
    # fill scale untouched.
    assert "fill" in out[1].aesthetics


# --------------------------- bump_aes_labels ---------------------------------


def test_bump_aes_labels_renames_key():
    labels = {"colour": "My Color", "x": "X"}
    out = bump_aes_labels(labels, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert out == {"colour_ggnewscale_1": "My Color", "x": "X"}


def test_bump_aes_labels_preserves_subclass_type():
    from ggplot2_py.labels import Labels

    labels = Labels(colour="My Color", x="X")
    out = bump_aes_labels(labels, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert isinstance(out, Labels)


def test_bump_aes_labels_idempotent_with_plot_marker():
    """A second bump for the same aesthetic must not double-rename."""

    class _FakePlot:
        pass

    plot = _FakePlot()
    labels = {"colour": "My Color"}
    out1 = bump_aes_labels(labels, original_aes="colour", new_aes="colour_ggnewscale_1", plot=plot)
    out2 = bump_aes_labels(out1, original_aes="colour", new_aes="colour_ggnewscale_99", plot=plot)
    # First rename happened; second should be a no-op because plot has the marker.
    assert "colour_ggnewscale_1" in out2
    assert "colour_ggnewscale_99" not in out2


def test_bump_aes_labels_none_returns_none():
    assert bump_aes_labels(None, "colour", "colour_ggnewscale_1") is None


# --------------------------- bump_aes_guides ---------------------------------


def test_bump_aes_guides_renames_key():
    g = gg.guide_legend()
    guides = {"colour": g, "fill": gg.guide_legend()}
    out = bump_aes_guides(guides, original_aes="colour", new_aes="colour_ggnewscale_1")
    assert "colour_ggnewscale_1" in out
    assert "colour" not in out
    assert "fill" in out  # untouched
    # new_aes appended to available_aes
    assert "colour_ggnewscale_1" in out["colour_ggnewscale_1"].available_aes


def test_bump_aes_guides_idempotent():
    g = gg.guide_legend()
    guides = {"colour": g}
    out1 = bump_aes_guides(guides, original_aes="colour", new_aes="colour_ggnewscale_1")
    # Bumping again for "colour" should be a no-op (no key named "colour" now).
    out2 = bump_aes_guides(out1, original_aes="colour", new_aes="colour_ggnewscale_99")
    assert out2 == out1


def test_bump_aes_guides_none_returns_none():
    assert bump_aes_guides(None, "colour", "colour_ggnewscale_1") is None
