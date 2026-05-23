"""ggnewscale-python — multiple fill and colour scales in ggplot2_py.

Python port of the R package ``ggnewscale`` (Elio Campitelli, GPL-3).
The plotting back-end is fixed to :mod:`ggplot2_py`; do **not** combine with
plotnine, matplotlib's pyplot API directly, seaborn, scanpy.pl, plotly,
altair, or bokeh — those backends diverge from R ggplot2's theme / font
metrics / guide layout / stat defaults.

Public API mirrors the R package 1:1:

- :func:`new_scale`  / :func:`new_scale_color` / :func:`new_scale_colour`
  / :func:`new_scale_fill` — open a new scale slot for a given aesthetic.
- :func:`rename_aes` — start a one-shot aesthetic rename.
- :func:`clear_aes` — end the rename started by :func:`rename_aes`.

Example
-------
.. code-block:: python

    import pandas as pd
    import ggplot2_py as gg
    from ggnewscale import new_scale_color

    df = pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1], "z": ["a", "b", "c"]})
    (
        gg.ggplot(df, gg.aes("x", "y"))
        + gg.geom_point(gg.aes(color="z"))
        + gg.scale_color_brewer(palette="Set1")
        + new_scale_color()
        + gg.geom_point(gg.aes(color="z"), size=3)
        + gg.scale_color_brewer(palette="Set2")
    )
"""

from __future__ import annotations

from . import _ggplot_add as _ggplot_add  # noqa: F401  (side-effect: registers handlers)
from ._markers import ClearAes, NewAes, RenameNext
from ._public import (
    clear_aes,
    new_scale,
    new_scale_color,
    new_scale_colour,
    new_scale_fill,
    rename_aes,
)
from ._scale_lookup import register_constructor, unregister_constructor

__version__ = "0.5.2.9000"
__r_commit__ = "3eb57c6"

__all__ = [
    # Version
    "__version__",
    "clear_aes",
    "new_scale",
    "new_scale_color",
    "new_scale_colour",
    "new_scale_fill",
    "rename_aes",
    # Re-export the marker classes for advanced users (e.g. registering
    # additional handlers on a plot subclass). The R package does not
    # export the equivalent S3 *classes*, but the Python idiom is to make
    # dispatch tags importable.
    "NewAes",
    "RenameNext",
    "ClearAes",
    # Extension hooks. R has no direct equivalents — they exist on the
    # Python side because Python lacks R's implicit search-list lookup
    # for user-defined scale_* / guide_* constructors.
    "register_constructor",
    "unregister_constructor",
]
