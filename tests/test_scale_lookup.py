"""Tests for the user-env scale lookup chain (Gap 1 fix).

R reference: ``R/rename-aes.R::find_global`` walks ``as.environment(-1)``
(globalenv) then ggplot2 namespace. We confirmed in a live R session that
defining ``scale_topo_continuous`` in user globals causes ggnewscale to
delegate to it from ``+ new_scale("topo")`` — this test suite enforces the
same on the Python side.
"""

from __future__ import annotations

import pandas as pd
import pytest

import ggplot2_py as gg
from ggnewscale import (
    new_scale,
    register_constructor,
    unregister_constructor,
)
from ggnewscale._scale_lookup import (
    capture_user_globals,
    find_global,
    find_scale,
)


# ----------------------- find_global --------------------------------------


def test_find_global_finds_ggplot2_py_function():
    fn = find_global("scale_colour_continuous")
    assert fn is gg.scale_colour_continuous


def test_find_global_returns_none_for_unknown_name():
    assert find_global("scale_definitely_not_a_real_aes_continuous") is None


def test_find_global_prefers_user_registry_over_ggplot2_py():
    sentinel = object()

    def fake_scale(**kwargs):
        return sentinel

    register_constructor("scale_colour_continuous", fake_scale)
    try:
        assert find_global("scale_colour_continuous") is fake_scale
    finally:
        unregister_constructor("scale_colour_continuous")

    # After cleanup the ggplot2_py original is found again.
    assert find_global("scale_colour_continuous") is gg.scale_colour_continuous


def test_find_global_uses_explicit_env_when_provided():
    def my_scale(**kwargs):
        return "from-env"

    fn = find_global("scale_topo_continuous", env={"scale_topo_continuous": my_scale})
    assert fn is my_scale


def test_find_global_env_takes_priority_over_ggplot2_py():
    # 'scale_colour_continuous' exists in ggplot2_py, but env wins.
    def shadow(**kwargs):
        return "shadow"

    fn = find_global("scale_colour_continuous", env={"scale_colour_continuous": shadow})
    assert fn is shadow


# ----------------------- capture_user_globals -----------------------------


def test_capture_user_globals_skips_ggnewscale_and_ggplot2_py():
    """When called from a test (this file), the captured globals are the
    test module's globals (NOT a ggnewscale or ggplot2_py frame)."""
    g = capture_user_globals()
    assert g is not None
    # The test module name should be in those globals (or pytest's framework).
    # At minimum, this module's __file__ should be in g.
    assert g.get("__file__", "").endswith("test_scale_lookup.py")


# ----------------------- find_scale with user env -------------------------


def test_find_scale_picks_up_user_defined_constructor_via_env():
    captured = []

    def scale_topo_continuous(**kwargs):
        captured.append(kwargs)
        # Delegate to a real ggplot2_py scale so the factory returns a Scale.
        return gg.scale_colour_continuous(**kwargs)

    factory = find_scale(
        new_aes="topo_ggnewscale_1",
        original_aes="topo",
        type_="continuous",
        env={"scale_topo_continuous": scale_topo_continuous},
    )
    assert factory is not None
    scale = factory()
    assert scale.aesthetics == ["topo_ggnewscale_1"]
    # And our hook was actually called.
    assert len(captured) >= 1


def test_find_scale_returns_none_when_no_constructor_visible():
    factory = find_scale(
        new_aes="nope_ggnewscale_1",
        original_aes="nope",
        type_="continuous",
        env={},  # explicitly empty
    )
    assert factory is None


# ----------------------- register_constructor end-to-end -------------------


def test_register_constructor_makes_custom_scale_visible_to_assign_scales():
    """Integration: registering scale_foo_continuous via the hook makes it
    available when ``+ new_scale("foo")`` calls ``assign_scales``.
    """
    call_log: list[str] = []

    def scale_foo_continuous(**kwargs):
        call_log.append("called")
        return gg.scale_colour_continuous(**kwargs)

    register_constructor("scale_foo_continuous", scale_foo_continuous)
    try:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1], "t": [0.1, 0.5, 0.9]})

        # Build a plot and add new_scale("foo"). The bumped slot will be
        # scale_foo_ggnewscale_1_continuous. When ggplot2_py later auto-picks
        # a default scale for the unrecognised aesthetic, it consults
        # plot.plot_env which we populated.
        p = (
            gg.ggplot(df, gg.aes("x", "y"))
            + gg.geom_point()
            + new_scale("foo")
        )

        looked_up = p.plot_env.lookup("scale_foo_ggnewscale_1_continuous")
        assert looked_up is not None
        # Invoke the registered factory through plot_env.
        scale = looked_up()
        assert scale.aesthetics == ["foo_ggnewscale_1"]
        # And the underlying user function was called.
        assert "called" in call_log
    finally:
        unregister_constructor("scale_foo_continuous")


def test_user_globals_picked_up_via_assign_scales_walk():
    """When ``scale_foo_continuous`` is defined at this test module's top-level
    (via globals().update), ``capture_user_globals`` returns the test's
    globals and ``find_scale`` should find it without explicit registration.
    """
    sentinel = []

    def scale_picked_up_continuous(**kwargs):
        sentinel.append(kwargs)
        return gg.scale_colour_continuous(**kwargs)

    # Inject into THIS module's globals.
    globals()["scale_picked_up_continuous"] = scale_picked_up_continuous
    try:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1]})
        p = (
            gg.ggplot(df, gg.aes("x", "y"))
            + gg.geom_point()
            + new_scale("picked_up")
        )
        looked_up = p.plot_env.lookup("scale_picked_up_ggnewscale_1_continuous")
        assert looked_up is not None
        scale = looked_up()
        assert scale.aesthetics == ["picked_up_ggnewscale_1"]
        assert len(sentinel) >= 1
    finally:
        del globals()["scale_picked_up_continuous"]
