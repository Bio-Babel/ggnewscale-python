"""Marker dataclasses for ggnewscale's ``ggplot + marker`` dispatch.

R reference: these correspond to the S3-classed objects returned by
``new_scale()``, ``rename_aes()``, and ``clear_aes()`` in
``R/new-scale.R`` and ``R/rename-aes.R``. The classes themselves carry no
behaviour — they exist so :func:`ggplot2_py.plot.update_ggplot` can
``singledispatch`` on their type at ``+`` time. Bodies live in
``_ggplot_add.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__: list[str] = []


@dataclass(frozen=True)
class NewAes:
    """Tag emitted by :func:`ggnewscale.new_scale` and its aliases.

    R counterpart: ``structure(standardise_aes_names(new_aes), class = "new_aes")``.

    Attributes
    ----------
    aes_name : str
        The standardised aesthetic name (e.g. ``"colour"`` or ``"fill"``).
    """

    aes_name: str


@dataclass(frozen=True)
class RenameNext:
    """Tag emitted by :func:`ggnewscale.rename_aes`.

    R counterpart::

        structure(<named character list>, class = "rename_next")

    The R value is a *named* character list; both the names and the values
    are aliased via ``standardise_aes_names``. We keep a single ``dict`` here,
    insertion-ordered (Python 3.7+ guarantees), so the ``mapping_items[0]``
    behaviour from ``+.ggplot_rename_next`` is reproducible.

    Attributes
    ----------
    mapping : dict[str, str]
        Mapping ``new_name -> original_aes`` (both names already standardised).
        Example: ``rename_aes(topo_color="color")`` becomes
        ``RenameNext({"topo_color": "colour"})`` (note the standardisation
        of the value).
    """

    mapping: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ClearAes:
    """Tag emitted by :func:`ggnewscale.clear_aes`.

    R counterpart: ``structure(NA, class = "clear_aes")``. A bare sentinel
    with no payload; routed by the ``rename_next`` pre-add hook (to
    short-circuit and self-unregister) and by ``@update_ggplot.register(ClearAes)``
    (a plain no-op when ``ClearAes`` is added to a vanilla plot).
    """
