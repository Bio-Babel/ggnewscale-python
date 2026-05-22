"""Generic name-replacement helper.

Mirrors ``R/utils.R::change_name`` (S3 generic with methods for ``character``,
``default``, and ``NULL``).

R behaviour:

- ``character`` (a bare string vector): replace VALUES equal to ``old`` with ``new``.
- ``default`` (anything with ``names()``, i.e. a named list / scale-aes-dict /
  mapping / labels / guides): replace NAMES (keys) equal to ``old`` with ``new``.
- ``NULL``: return ``NULL`` (Python: ``None``).

Python translation uses :func:`functools.singledispatch`. The ``character``
branch is special-cased for ``list[str]`` / ``tuple[str]``; the ``default``
branch covers any ``dict``-like mapping. Anything else (e.g. ``None``) falls
through to the base dispatcher which returns the input unchanged — matching
the R ``NULL`` semantics.
"""

from __future__ import annotations

from functools import singledispatch
from typing import Any, Iterable

__all__: list[str] = []


def _replace_values(seq: Iterable[str], old: Iterable[str], new: str) -> list[str]:
    old_set = set(old) if not isinstance(old, str) else {old}
    return [new if v in old_set else v for v in seq]


def _replace_keys(d: dict, old: Iterable[str], new: str) -> dict:
    old_set = set(old) if not isinstance(old, str) else {old}
    # Preserve insertion order; replace each matching key with new (one-to-one).
    out: dict = {}
    for k, v in d.items():
        out[new if k in old_set else k] = v
    return out


@singledispatch
def change_name(obj: Any, old: Any, new: str) -> Any:
    """Replace names/values in *obj* matching *old* with *new*.

    The base implementation is the ``NULL`` branch from R: return the input
    unchanged. Concrete subclasses (``list``, ``tuple``, ``dict``) are
    handled by registered overloads below.
    """
    if obj is None:
        return None
    # Unknown type: behave like R's default (try to rename names).
    if hasattr(obj, "items") and callable(obj.items):
        return _replace_keys(dict(obj), old, new)
    return obj


@change_name.register(str)
def _change_name_str(obj: str, old: Any, new: str) -> str:
    """``character`` branch for a length-1 vector.

    R treats a bare string as a character vector of length 1, so
    ``change_name.character("colour", "colour", "fill")`` returns ``"fill"``.
    The Python equivalent must match: return *new* iff *obj* equals
    (or is contained in) *old*, else return *obj* unchanged.

    R reference: ``R/utils.R::change_name.character``.
    """
    if isinstance(old, str):
        return new if obj == old else obj
    # Iterable of strings (e.g. list/tuple of "old" values).
    try:
        return new if obj in set(old) else obj
    except TypeError:
        return new if obj == old else obj


@change_name.register(list)
def _change_name_list(obj: list, old: Any, new: str) -> list:
    """``character`` branch: replace values that appear in *old* with *new*."""
    return _replace_values(obj, old, new)


@change_name.register(tuple)
def _change_name_tuple(obj: tuple, old: Any, new: str) -> tuple:
    """``character`` branch for tuple — Geom slots like ``required_aes`` are tuples."""
    return tuple(_replace_values(obj, old, new))


@change_name.register(dict)
def _change_name_dict(obj: dict, old: Any, new: str) -> dict:
    """``default`` branch: replace keys that appear in *old* with *new*.

    Returns a new dict of the same concrete type when subclass round-trips
    via ``type(obj)(...)`` (e.g. ``Mapping`` and ``Labels`` are ``dict`` subclasses).
    """
    renamed = _replace_keys(obj, old, new)
    cls = type(obj)
    if cls is dict:
        return renamed
    try:
        return cls(renamed)  # type: ignore[call-arg]
    except TypeError:
        return cls(**renamed)  # type: ignore[call-arg]


@change_name.register(type(None))
def _change_name_none(obj: None, old: Any, new: str) -> None:
    return None
