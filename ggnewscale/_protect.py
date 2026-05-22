"""Protection markers preventing double-renaming of already-bumped objects.

R reference: ``R/utils.R::protect`` / ``is_protected`` (S3 generics).

R uses two storage strategies depending on the dispatched class:

- ``protect.default(object, aes)`` writes ``object$ggnewscale_renamed``
  (a slot on the ggproto / list object).
- ``protect.character(object, aes)`` writes
  ``attr(object, "ggnewscale_renamed")`` (an R attribute on the string).

Python strings/lists do not have a per-instance attribute slot, and Python
lists do not have a stable identity to key against. The ggnewscale porting
contract (essential_suggestions.md §3) routes the marker as follows:

* ggproto instances (Layer / Geom / Stat / Scale / Guide) — instance
  attribute ``obj._ggnewscale_renamed`` (a ``set[str]``).
* character vectors (``scale.aesthetics``, label strings) — the marker is
  stashed on the *owning object* by the caller (e.g. on the Scale instead
  of the aes-list; on the Plot instead of the label string). This module
  therefore exposes a small, uniform "instance attribute" API and the
  caller decides what the owning instance is.

Use :func:`set_protected` and :func:`is_protected` from porting code.
"""

from __future__ import annotations

from typing import Any, Iterable

__all__: list[str] = []

_ATTR = "_ggnewscale_renamed"


def _as_set(aes: str | Iterable[str]) -> set[str]:
    if isinstance(aes, str):
        return {aes}
    return set(aes)


def set_protected(obj: Any, aes: str | Iterable[str]) -> Any:
    """Mark *obj* as protected for the aesthetic *aes*.

    R ref: ``protect`` (S3 generic).

    Parameters
    ----------
    obj : Any
        The object to protect — typically a ``ggplot2_py`` Layer / Geom /
        Stat / Scale / Guide instance. For protecting label *values*, pass
        the owning *plot*, not the label string itself (per ggnewscale
        porting contract §3).
    aes : str or iterable of str
        Aesthetic name(s) to add to *obj*'s protected set.

    Returns
    -------
    Any
        *obj* (for chaining). Mutates the instance in place.
    """
    current: set[str] = getattr(obj, _ATTR, set())
    if not isinstance(current, set):
        # Defensive: in case an alien type sneaked a list/tuple in.
        current = set(current)
    current = current | _as_set(aes)
    setattr(obj, _ATTR, current)
    return obj


def is_protected(obj: Any, aes: str) -> bool:
    """Return ``True`` iff *obj* has been marked protected for aesthetic *aes*.

    R ref: ``is_protected`` (S3 generic).

    Parameters
    ----------
    obj : Any
        The object whose protected set is queried.
    aes : str
        Aesthetic name to look up.
    """
    return aes in getattr(obj, _ATTR, set())
