"""Constructor tests for the six R-API exports.

Cross-validated against R behaviour (``Rscript`` runs of the same call).
"""

from __future__ import annotations

import pytest

import ggnewscale
from ggnewscale import (
    ClearAes,
    NewAes,
    RenameNext,
    clear_aes,
    new_scale,
    new_scale_color,
    new_scale_colour,
    new_scale_fill,
    rename_aes,
)


def test_new_scale_standardises_color_to_colour():
    # R: new_scale("color") -> structure("colour", class="new_aes")
    out = new_scale("color")
    assert isinstance(out, NewAes)
    assert out.aes_name == "colour"


def test_new_scale_passthrough_for_already_canonical():
    out = new_scale("fill")
    assert isinstance(out, NewAes)
    assert out.aes_name == "fill"


def test_new_scale_color_and_colour_aliases_identical():
    # Both spellings must exist (porting contract §0.3) and produce the same payload.
    assert new_scale_color() == new_scale_colour() == NewAes("colour")


def test_new_scale_fill_alias():
    assert new_scale_fill() == NewAes("fill")


def test_rename_aes_standardises_keys_and_values():
    # R: rename_aes(topo_color = "color") -> standardised both sides.
    out = rename_aes(topo_color="color")
    assert isinstance(out, RenameNext)
    # Keys: "topo_color" -> "topo_colour" (US -> UK).
    # Values: "color" -> "colour".
    assert out.mapping == {"topo_colour": "colour"}


def test_rename_aes_empty():
    out = rename_aes()
    assert isinstance(out, RenameNext)
    assert out.mapping == {}


def test_rename_aes_preserves_order_for_first_pair_semantics():
    # R consumes only rename_aes[[1]]; preserving insertion order is essential.
    out = rename_aes(a="fill", b="color")
    keys = list(out.mapping.keys())
    assert keys[0] == "a"


def test_clear_aes_returns_clear_aes_instance():
    out = clear_aes()
    assert isinstance(out, ClearAes)


def test_top_level_dunder_all_lists_six_R_exports_classes_and_extension_hooks():
    expected = {
        # Six R-API functions.
        "clear_aes",
        "new_scale",
        "new_scale_color",
        "new_scale_colour",
        "new_scale_fill",
        "rename_aes",
        # Marker classes (Python-side dispatch tags; not in R NAMESPACE).
        "NewAes",
        "RenameNext",
        "ClearAes",
        # Extension hooks for user-defined scale_* / guide_* constructors.
        # No R equivalent — Python lacks R's implicit search-list lookup.
        "register_constructor",
        "unregister_constructor",
        # Package version (PEP 396 convention; not an R concept).
        "__version__",
    }
    assert set(ggnewscale.__all__) == expected
