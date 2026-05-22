"""Aesthetic-name helpers for the ggnewscale port.

Mirrors ``R/utils.R::aes_name`` and ``remove_new``.
"""

from __future__ import annotations

import re

__all__: list[str] = []

_GGNEWSCALE_SUFFIX = re.compile(r"_ggnewscale_\d+")


def aes_name(aes: str, scale_number: int) -> str:
    """Produce ``"<aes>_ggnewscale_<n>"``.

    R ref: ``R/utils.R``::``aes_name``.

    Parameters
    ----------
    aes : str
        The original aesthetic name (already standardised, e.g. ``"colour"``).
    scale_number : int
        The N-th time ``new_scale(aes)`` has been added; 1-based.

    Returns
    -------
    str
        The mangled aesthetic name used internally to keep multiple scales
        of the same kind from colliding.
    """
    return f"{aes}_ggnewscale_{scale_number}"


def remove_new(aes: str) -> str:
    """Strip the ``"_ggnewscale_<n>"`` suffix from a possibly-mangled aesthetic name.

    R ref: ``R/utils.R``::``remove_new``.

    Parameters
    ----------
    aes : str
        The (possibly mangled) aesthetic name.

    Returns
    -------
    str
        The original aesthetic name; unchanged if no mangling suffix is present.
    """
    return _GGNEWSCALE_SUFFIX.sub("", aes)
