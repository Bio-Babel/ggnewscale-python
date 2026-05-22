"""User-facing constructors mirroring the six R exports.

R reference: ``R/new-scale.R`` and ``R/rename-aes.R``.
"""

from __future__ import annotations

import ggplot2_py as _gg

from ._markers import ClearAes, NewAes, RenameNext

__all__ = [
    "clear_aes",
    "new_scale",
    "new_scale_color",
    "new_scale_colour",
    "new_scale_fill",
    "rename_aes",
]


def _standardise_one(name: str) -> str:
    """Standardise a single aesthetic name (UK spelling, canonical synonyms)."""
    out = _gg.standardise_aes_names([name])
    return out[0]


def new_scale(new_aes: str) -> NewAes:
    """Open a new scale slot for the aesthetic *new_aes*.

    R counterpart::

        new_scale <- function(new_aes) {
          structure(ggplot2::standardise_aes_names(new_aes), class = "new_aes")
        }

    Adding the returned ``NewAes`` to a plot via ``ggplot + new_scale("colour")``
    triggers ``ggplot_add.new_aes``, which renames every existing layer's,
    scale's, label's and guide's occurrence of *new_aes* to
    ``"<new_aes>_ggnewscale_<n>"`` so subsequent ``+ geom_*`` and
    ``+ scale_<aes>_*`` additions bind to a fresh slot.

    Parameters
    ----------
    new_aes : str
        Aesthetic name (e.g. ``"colour"``, ``"fill"``, ``"color"`` —
        US spelling is mapped to UK via :func:`ggplot2_py.standardise_aes_names`).

    Returns
    -------
    NewAes
        Dispatch tag consumed by ``@update_ggplot.register(NewAes)``.
    """
    return NewAes(aes_name=_standardise_one(new_aes))


def new_scale_color() -> NewAes:
    """Alias for :func:`new_scale` with ``new_aes="color"``.

    Standardisation collapses ``"color"`` to ``"colour"``, so this is identical
    to :func:`new_scale_colour`. Both spellings are kept because R users
    copy-paste examples using either (porting contract §0.3).
    """
    return new_scale("colour")


def new_scale_colour() -> NewAes:
    """Alias for :func:`new_scale` with ``new_aes="colour"``."""
    return new_scale("colour")


def new_scale_fill() -> NewAes:
    """Alias for :func:`new_scale` with ``new_aes="fill"``."""
    return new_scale("fill")


def rename_aes(**kwargs: str) -> RenameNext:
    """Open a one-shot aesthetic rename.

    R counterpart::

        rename_aes <- function(...) {
          aes <- list(...)
          names(aes) <- ggplot2::standardise_aes_names(names(aes))
          aes <- lapply(aes, ggplot2::standardise_aes_names)
          structure(aes, class = "rename_next")
        }

    Both the keys and the values are passed through
    :func:`ggplot2_py.standardise_aes_names`. The result must be added to a
    plot *immediately* before the layer or scale being renamed; the next
    ``+`` consumes the rename and ``clear_aes()`` (or completion of a single
    ``+ layer/scale`` step) tears it down.

    Note
    ----
    R's ``+.ggplot_rename_next`` only consumes the **first** pair
    (``rename_aes[[1]]``, ``names(rename_aes)[[1]]``); subsequent pairs are
    silently ignored. The Python implementation mirrors this quirk exactly.

    Parameters
    ----------
    **kwargs : str
        Mapping ``new_name=original_aes``. Example:
        ``rename_aes(topo_color="color")`` re-routes the next layer's
        ``topo_color`` aesthetic to a fresh ``colour`` slot.

    Returns
    -------
    RenameNext
    """
    if not kwargs:
        return RenameNext(mapping={})

    keys = list(kwargs.keys())
    values = list(kwargs.values())
    std_keys = _gg.standardise_aes_names(keys)
    std_values = [_standardise_one(v) for v in values]
    return RenameNext(mapping=dict(zip(std_keys, std_values)))


def clear_aes() -> ClearAes:
    """End the rename started by :func:`rename_aes`.

    R counterpart::

        clear_aes <- function() {
          structure(NA, class = "clear_aes")
        }

    When added to a plot that has an active ``RenameNext``, the registered
    pre-add hook short-circuits (returning ``None``) and unregisters itself.
    When added to a plot with no active rename, it is a no-op.

    Returns
    -------
    ClearAes
    """
    return ClearAes()
