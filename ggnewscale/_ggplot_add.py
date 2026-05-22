"""``ggplot_add`` dispatchers and the pre-add hook for ``rename_next``.

R reference: ``R/ggplot-add.R`` and ``R/rename-aes.R``::``+.ggplot_rename_next``.

Importing this module has the side effect of registering three handlers on
:func:`ggplot2_py.plot.update_ggplot`. The :mod:`ggnewscale.__init__` module
imports this module purely for that side effect.
"""

from __future__ import annotations

from typing import Any

import ggplot2_py as _gg
from ggplot2_py.plot import (
    register_pre_add_hook,
    unregister_pre_add_hook,
    update_ggplot,
)

from ._bump import (
    bump_aes_guides,
    bump_aes_labels,
    bump_aes_layer,
    bump_aes_layers,
    bump_aes_scale,
    bump_aes_scales,
)
from ._aes import aes_name
from ._markers import ClearAes, NewAes, RenameNext
from ._scale_lookup import assign_scales

__all__: list[str] = []


# ---------------------------------------------------------------------------
# new_scale  (R: ggplot_add.new_aes)
# ---------------------------------------------------------------------------


_COUNTERS_ATTR = "_ggnewscale_scales"
_RENAME_STATE_ATTR = "_ggnewscale_rename_state"


def _get_private(plot: Any, name: str, default: Any = None) -> Any:
    """Read an underscore-prefixed private attribute on a ``GGPlot`` instance.

    ``GGPlot.__getattr__`` raises ``AttributeError`` for any name starting
    with ``_``, so we read via ``object.__getattribute__`` to bypass it.
    """
    try:
        return object.__getattribute__(plot, name)
    except AttributeError:
        return default


def _set_private(plot: Any, name: str, value: Any) -> None:
    """Write an underscore-prefixed private attribute on a ``GGPlot`` instance.

    ``GGPlot.__setattr__`` routes unknown names into ``_meta``; we bypass it
    so the attribute lives in the instance's own ``__dict__`` and survives
    ``copy.copy(plot)`` cleanly across the ``+`` clone chain.
    """
    object.__setattr__(plot, name, value)


@update_ggplot.register(NewAes)
def _add_new_aes(obj: NewAes, plot: Any, object_name: str = "") -> Any:
    """Apply a fresh aesthetic slot to *plot*.

    R counterpart::

        ggplot_add.new_aes <- function(object, plot, ...) {
          scale_number <- (plot$ggnewscale_scales[[object]] %||% 0) + 1
          new_aes <- aes_name(object, scale_number)
          plot <- assing_scales(new_aes = new_aes, original_aes = object, plot)
          ...
        }
    """
    original_aes = obj.aes_name

    counters: dict[str, int] = dict(_get_private(plot, _COUNTERS_ATTR) or {})
    scale_number = counters.get(original_aes, 0) + 1
    new_aes = aes_name(original_aes, scale_number)

    plot = assign_scales(new_aes=new_aes, original_aes=original_aes, plot=plot)

    # Global mapping rename
    if plot.mapping is not None and original_aes in plot.mapping:
        mapping_cls = type(plot.mapping)
        new_mapping_data = dict(plot.mapping)
        new_mapping_data[new_aes] = new_mapping_data.pop(original_aes)
        try:
            plot.mapping = mapping_cls(new_mapping_data)
        except TypeError:
            plot.mapping = mapping_cls(**new_mapping_data)

    plot.layers = bump_aes_layers(plot.layers, original_aes=original_aes, new_aes=new_aes)

    if plot.scales is not None and hasattr(plot.scales, "scales") and plot.scales.scales:
        plot.scales.scales = bump_aes_scales(
            plot.scales.scales, original_aes=original_aes, new_aes=new_aes
        )

    plot.labels = bump_aes_labels(plot.labels, original_aes=original_aes, new_aes=new_aes, plot=plot)

    if plot.guides is not None and hasattr(plot.guides, "guides") and plot.guides.guides:
        plot.guides.guides = bump_aes_guides(
            plot.guides.guides, original_aes=original_aes, new_aes=new_aes
        )

    counters[original_aes] = scale_number
    _set_private(plot, _COUNTERS_ATTR, counters)
    return plot


# ---------------------------------------------------------------------------
# clear_aes  (R: ggplot_add.clear_aes — no-op when added to a plain plot)
# ---------------------------------------------------------------------------


@update_ggplot.register(ClearAes)
def _add_clear_aes(obj: ClearAes, plot: Any, object_name: str = "") -> Any:
    """No-op when ``ClearAes`` lands on a plot with no active rename.

    The "real" teardown happens inside the pre-add hook (registered by
    :func:`_add_rename_next`) when the hook sees a ``ClearAes`` as the next
    *other* argument and self-unregisters.

    R counterpart::

        ggplot_add.clear_aes <- function(object, plot, ...) plot
    """
    return plot


# ---------------------------------------------------------------------------
# rename_aes  (R: ggplot_add.rename_next + `+.ggplot_rename_next`)
# ---------------------------------------------------------------------------


@update_ggplot.register(RenameNext)
def _add_rename_next(obj: RenameNext, plot: Any, object_name: str = "") -> Any:
    """Stage a one-shot aesthetic rename.

    R counterpart::

        ggplot_add.rename_next <- function(object, plot, ...) {
          class(plot) <- c("ggplot_rename_next", class(plot))
          plot$rename_aes <- object
          plot
        }

    Implementation: stash the mapping on the plot and install a pre-add hook
    that intercepts the *next* ``+``. The hook self-unregisters on
    ``ClearAes`` (one-shot teardown).
    """
    _set_private(plot, _RENAME_STATE_ATTR, dict(obj.mapping))

    def _hook(plot_inner: Any, other: Any) -> Any:
        # R's "+.ggplot_rename_next" body, restructured for the
        # register_pre_add_hook contract.
        if isinstance(other, ClearAes):
            unregister_pre_add_hook(plot_inner, _hook)
            _set_private(plot_inner, _RENAME_STATE_ATTR, None)
            return None

        mapping = _get_private(plot_inner, _RENAME_STATE_ATTR) or {}
        if not mapping:
            unregister_pre_add_hook(plot_inner, _hook)
            return other

        # R: rename_aes[[1]], names(rename_aes)[[1]] — only the first pair.
        new_name, original = next(iter(mapping.items()))

        Layer = getattr(_gg, "Layer", None)
        Scale = getattr(_gg, "Scale", None)

        if Layer is not None and isinstance(other, Layer):
            other = bump_aes_layer(other, original_aes=original, new_aes=new_name)
            assign_scales(new_aes=new_name, original_aes=original, plot=plot_inner)

        if Scale is not None and isinstance(other, Scale):
            other = bump_aes_scale(other, original_aes=original, new_aes=new_name)

        return other

    register_pre_add_hook(plot, _hook)
    return plot
