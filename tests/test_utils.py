"""Tests for ggnewscale's utility helpers (_aes / _change_name / _protect).

Cross-validated against the R reference (``R/utils.R``).
"""

from __future__ import annotations

import pytest

from ggnewscale._aes import aes_name, remove_new
from ggnewscale._change_name import change_name
from ggnewscale._protect import is_protected, set_protected


# -------------------------- aes_name / remove_new --------------------------

def test_aes_name_matches_R_format():
    # R: aes_name("colour", 1) -> "colour_ggnewscale_1"
    assert aes_name("colour", 1) == "colour_ggnewscale_1"
    assert aes_name("fill", 3) == "fill_ggnewscale_3"


def test_remove_new_strips_suffix():
    # R: remove_new("colour_ggnewscale_2") -> "colour"
    assert remove_new("colour_ggnewscale_2") == "colour"
    assert remove_new("colour") == "colour"  # unchanged when no suffix
    # multiple suffixes (defensive)
    assert remove_new("colour_ggnewscale_1_ggnewscale_2") == "colour"


# ----------------------------- change_name --------------------------------

def test_change_name_on_list_replaces_values():
    # R: change_name.character(c("colour", "fill", "x"), "colour", "colour_ggnewscale_1")
    out = change_name(["colour", "fill", "x"], "colour", "colour_ggnewscale_1")
    assert out == ["colour_ggnewscale_1", "fill", "x"]


def test_change_name_on_tuple_replaces_values_preserving_type():
    out = change_name(("size", "shape", "colour"), "colour", "colour_ggnewscale_1")
    assert out == ("size", "shape", "colour_ggnewscale_1")
    assert isinstance(out, tuple)


def test_change_name_on_dict_replaces_keys():
    # R: change_name.default(list(colour="z", x="x"), "colour", "colour_ggnewscale_1")
    out = change_name({"colour": "z", "x": "x"}, "colour", "colour_ggnewscale_1")
    assert out == {"colour_ggnewscale_1": "z", "x": "x"}


def test_change_name_on_dict_preserves_order():
    out = change_name({"a": 1, "b": 2, "c": 3}, "b", "bb")
    assert list(out.keys()) == ["a", "bb", "c"]


def test_change_name_on_none_returns_none():
    assert change_name(None, "colour", "colour_ggnewscale_1") is None


def test_change_name_with_iterable_old_list():
    # R: change_name accepts a length-N character vector for "old"
    out = change_name(["a", "b", "c", "d"], ["a", "c"], "x")
    assert out == ["x", "b", "x", "d"]


def test_change_name_on_bare_string_matches_replaces():
    # R: change_name.character("colour", "colour", "fill") -> "fill"
    assert change_name("colour", "colour", "fill") == "fill"


def test_change_name_on_bare_string_no_match_returns_unchanged():
    # R: change_name.character("colour", "fill", "blue") -> "colour"
    assert change_name("colour", "fill", "blue") == "colour"


def test_change_name_on_bare_string_with_iterable_old():
    # R: change_name.character("colour", c("colour", "fill"), "renamed") -> "renamed"
    assert change_name("colour", ["colour", "fill"], "renamed") == "renamed"
    assert change_name("size", ["colour", "fill"], "renamed") == "size"


def test_change_name_returns_same_subclass_for_dict_subclass():
    class Sub(dict):
        pass

    out = change_name(Sub({"x": 1, "y": 2}), "x", "xx")
    assert isinstance(out, Sub)
    assert dict(out) == {"xx": 1, "y": 2}


# ----------------------------- _protect ------------------------------------

class _FakeProtoLike:
    """Stand-in for a ggproto instance (just an object with a writable __dict__)."""


def test_set_protected_then_is_protected_returns_true():
    obj = _FakeProtoLike()
    set_protected(obj, "colour")
    assert is_protected(obj, "colour")
    assert not is_protected(obj, "fill")


def test_set_protected_accumulates_set_union():
    obj = _FakeProtoLike()
    set_protected(obj, "colour")
    set_protected(obj, ["fill", "colour"])
    assert is_protected(obj, "colour")
    assert is_protected(obj, "fill")
    # Unique (no duplicates accumulated)
    assert getattr(obj, "_ggnewscale_renamed") == {"colour", "fill"}


def test_is_protected_when_attr_missing_is_false():
    assert not is_protected(_FakeProtoLike(), "colour")


def test_set_protected_returns_obj_for_chaining():
    obj = _FakeProtoLike()
    out = set_protected(obj, "colour")
    assert out is obj
