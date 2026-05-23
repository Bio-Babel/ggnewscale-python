"""Layer / scale / label / guide aesthetic-bumping helpers.

R reference: ``R/bump-aes-layers.R``, ``R/bump-aes-scales.R``,
``R/bump-aes-labels.R``, ``R/bump-aes-guides.R``.

Each ``bump_aes_*`` function takes a slot from a :class:`ggplot2_py.GGPlot`
and rewrites every occurrence of the *original* aesthetic name (e.g.
``"colour"``) to a freshly-coined *new* aesthetic name (e.g.
``"colour_ggnewscale_1"``). Already-bumped objects are skipped via the
:mod:`._protect` markers.

The helpers also produce **clones** of every nested ggproto (layer, geom,
stat, scale, guide) so previously-added scale layers keep their old aes
names — see the *previous layers don't change* test from
``R/tests/testthat/test-newscale.R``.
"""

from __future__ import annotations

import copy
from typing import Any, Iterable

import ggplot2_py as _gg

from ._change_name import change_name
from ._protect import is_protected, set_protected

__all__: list[str] = []


# ---------------------------------------------------------------------------
# Layer bumping
# ---------------------------------------------------------------------------


def bump_aes_layer(layer: Any, original_aes: str, new_aes: str) -> Any:
    """Clone *layer* with every reference to *original_aes* renamed to *new_aes*.

    R counterpart: ``bump_aes_layer`` in ``R/bump-aes-layers.R``.

    Parameters
    ----------
    layer : ggplot2_py.Layer
        The layer to bump. Returned unchanged (just cloned) if it does not
        use *original_aes* or if it has already been protected for it.
    original_aes : str
        Original aesthetic name on the layer (e.g. ``"colour"``).
    new_aes : str
        Replacement aesthetic name (e.g. ``"colour_ggnewscale_1"``).

    Returns
    -------
    ggplot2_py.Layer
        A clone of *layer*; the original is **not** mutated.
    """
    # 1. Don't touch already-renamed layers
    if is_protected(layer, original_aes):
        return layer

    # 2. Clone the layer
    new_layer = _gg.ggproto(None, layer)

    # 3. Find the actual aes name to rename (explicit mapping, else default).
    mapping_keys = list(new_layer.mapping.keys()) if new_layer.mapping is not None else []
    old_aes_list: list[str] = [k for k in mapping_keys if k == original_aes]

    if not old_aes_list:
        stat_default = _safe_default_aes(new_layer.stat)
        old_aes_list = [k for k in stat_default.keys() if k == original_aes]
        if not old_aes_list:
            geom_default = _safe_default_aes(new_layer.geom)
            old_aes_list = [k for k in geom_default.keys() if k == original_aes]

    # 4. If layer doesn't use the aesthetic at all, return unchanged.
    if not old_aes_list:
        return new_layer

    # In R old_aes is a length-1 vector; we follow suit and pick the first match.
    old_aes = old_aes_list[0]

    # 5. Build a renamed Geom.
    old_geom = new_layer.geom
    old_handle_na = getattr(old_geom, "handle_na", None)
    new_geom_kwargs: dict[str, Any] = {}

    if old_handle_na is not None:
        def _new_handle_na(self: Any, data: Any, params: Any) -> Any:
            """Column-rename shim around the inner geom's handle_na.

            Renames ``new_aes`` -> ``original_aes`` in the data columns so the
            inner geom (which still thinks in original-aes terms) sees what
            it expects, then delegates.
            """
            renamed_data = _rename_columns(data, {new_aes: original_aes})
            return old_handle_na(renamed_data, params)

        new_geom_kwargs["handle_na"] = _new_handle_na

    new_geom = _gg.ggproto(f"New{type(old_geom).__name__}", old_geom, **new_geom_kwargs)

    # Slot rewrites on the new geom.
    new_geom.default_aes = change_name(_safe_default_aes(new_geom), old_aes, new_aes)
    new_geom.non_missing_aes = change_name(
        _safe_aes_slot(new_geom, "non_missing_aes"), old_aes, new_aes
    )
    new_geom.required_aes = change_name(
        _safe_aes_slot(new_geom, "required_aes"), old_aes, new_aes
    )
    new_geom.optional_aes = change_name(
        _safe_aes_slot(new_geom, "optional_aes"), old_aes, new_aes
    )

    # draw_key column-rename shim.
    #
    # ggplot2_py's ``draw_key_*`` helpers are installed on Geom instances as
    # bound methods even though their underlying signatures don't begin with
    # ``self`` — calling ``geom.draw_key(data, params, size)`` directly errors
    # with arity-mismatch (see guide_legend.py:243-252 for ggplot2_py's own
    # ``__func__`` fallback). To mirror R's ``new_geom$draw_key <- new_draw_key``
    # we capture the raw function (via ``__func__`` if available) and install
    # the wrapper bypassing the auto-bind so subsequent calls remain plain.
    old_draw_key_attr = getattr(new_geom, "draw_key", None)
    if old_draw_key_attr is not None:
        old_draw_key_fn = getattr(old_draw_key_attr, "__func__", old_draw_key_attr)

        def _new_draw_key(data: Any, params: Any, size: Any = None, _fn: Any = old_draw_key_fn) -> Any:
            renamed_data = _rename_columns(data, {new_aes: original_aes})
            return _fn(renamed_data, params, size)

        # Install as a plain attribute via object.__setattr__ to skip
        # GGProto's auto-bind (which would prepend self and reintroduce
        # the arity bug).
        object.__setattr__(new_geom, "draw_key", _new_draw_key)

    new_layer.geom = new_geom

    # 6. Build a renamed Stat. R uses an `is_new` flag to avoid stacking
    #    wrap layers in the inheritance chain — we mirror it.
    old_stat = new_layer.stat
    parent_stat = old_stat.super() if getattr(old_stat, "is_new", False) else _gg.ggproto(None, old_stat)

    def _new_setup_data(self: Any, data: Any, params: Any) -> Any:
        # Mirrors R: rename to original, delegate to parent, rename back.
        # R also passes scales through; ggplot2_py's setup_data signature is
        # (data, params) — no scales — so we drop that arg.
        renamed_data = _rename_columns(data, {new_aes: original_aes})
        out = _gg.ggproto_parent(self.super(), self).setup_data(renamed_data, params)
        return _rename_columns(out, {original_aes: new_aes})

    def _new_stat_handle_na(self: Any, data: Any, params: Any) -> Any:
        # Mirrors R/bump-aes-layers.R:64-67. ggplot2_py's base Stat does NOT
        # currently expose handle_na (only Geom does), but we install the
        # wrap for R parity: when/if a future ggplot2_py adds it, the wrap
        # is already in place so column-name renaming flows through the
        # parent chain consistently. The defensive ``hasattr`` check keeps
        # the wrap inert today while staying faithful to R's algorithm.
        renamed_data = _rename_columns(data, {new_aes: original_aes})
        parent_proxy = _gg.ggproto_parent(self.super(), self)
        parent_handle_na = getattr(parent_proxy, "handle_na", None)
        if parent_handle_na is None:
            return renamed_data
        return parent_handle_na(renamed_data, params)

    new_stat = _gg.ggproto(
        f"New{type(old_stat).__name__}",
        parent_stat,
        setup_data=_new_setup_data,
        handle_na=_new_stat_handle_na,
        is_new=True,
    )

    new_stat.default_aes = change_name(_safe_default_aes(new_stat), old_aes, new_aes)
    new_stat.non_missing_aes = change_name(
        _safe_aes_slot(new_stat, "non_missing_aes"), old_aes, new_aes
    )
    new_stat.required_aes = change_name(
        _safe_aes_slot(new_stat, "required_aes"), old_aes, new_aes
    )
    new_stat.optional_aes = change_name(
        _safe_aes_slot(new_stat, "optional_aes"), old_aes, new_aes
    )

    new_layer.stat = new_stat

    # 7. Mapping & aes_params name-rewrites.
    #    If the mapping is implicit, R copies the stat's default mapping value
    #    into the explicit mapping. This fixes ggnewscale #45.
    new_mapping = dict(new_layer.mapping) if new_layer.mapping is not None else {}
    if old_aes not in new_mapping:
        stat_default = _safe_default_aes(new_stat)
        if new_aes in stat_default:
            new_mapping[old_aes] = stat_default[new_aes]
    new_mapping = change_name(new_mapping, old_aes, new_aes)
    new_layer.mapping = _mapping_like(new_layer.mapping, new_mapping)

    if new_layer.aes_params:
        new_layer.aes_params = change_name(dict(new_layer.aes_params), old_aes, new_aes)

    # 8. Preserve custom Python attributes on the layer (test:
    #    "custom attributes are retained").
    _copy_extra_attrs(src=layer, dst=new_layer)

    # 9. Mark as protected so subsequent bumps for this aes are no-ops.
    set_protected(new_layer, original_aes)
    return new_layer


def bump_aes_layers(layers: list, original_aes: str, new_aes: str) -> list:
    """Apply :func:`bump_aes_layer` to every layer in *layers*.

    Returns
    -------
    list
        New list of bumped (cloned) layers.
    """
    return [bump_aes_layer(layer, original_aes, new_aes) for layer in layers]


# ---------------------------------------------------------------------------
# Scale bumping
# ---------------------------------------------------------------------------


def bump_aes_scale(scale: Any, original_aes: str, new_aes: str) -> Any:
    """Rewrite a scale to bind to *new_aes* instead of *original_aes*.

    R counterpart: ``bump_aes_scale`` in ``R/bump-aes-scales.R``.
    """
    if scale is None:
        return scale
    if is_protected(scale, original_aes):
        return scale

    aesthetics = list(scale.aesthetics or [])
    old_aes_present = [a for a in aesthetics if a == original_aes]

    if old_aes_present:
        scale.aesthetics = [new_aes if a == original_aes else a for a in aesthetics]

        no_guide = _is_no_guide(scale.guide)

        if not no_guide:
            # Materialise a character-named guide into a Guide ggproto.
            if isinstance(scale.guide, str):
                guide_fn = _resolve_guide_constructor(scale.guide)
                if guide_fn is not None:
                    scale.guide = guide_fn()

            if _is_guide_proto(scale.guide):
                old = scale.guide
                new = _gg.ggproto(None, old)

                new.available_aes = change_name(
                    _safe_aes_slot(new, "available_aes"), old_aes_present, new_aes
                )
                # Also ensure new_aes is present even if it wasn't in the
                # original available_aes (mirrors R: `<- new_aes` direct assign).
                if isinstance(new.available_aes, list):
                    new.available_aes = [new_aes if a in old_aes_present else a for a in new.available_aes]
                elif isinstance(new.available_aes, tuple):
                    new.available_aes = tuple(
                        new_aes if a in old_aes_present else a for a in new.available_aes
                    )

                # Update aesthetic override stored in guide.params['override.aes'] /
                # guide.params['override_aes'] (both naming conventions exist).
                params = getattr(new, "params", None)
                if params is not None:
                    for key in ("override.aes", "override_aes"):
                        if key in params and params[key]:
                            params[key] = change_name(dict(params[key]), old_aes_present, new_aes)

                scale.guide = new
            else:
                # Plain object — try rewriting available_aes / override.aes.
                guide = scale.guide
                if hasattr(guide, "available_aes"):
                    guide.available_aes = change_name(
                        guide.available_aes, old_aes_present, new_aes
                    )
                if hasattr(guide, "override_aes") and guide.override_aes:
                    guide.override_aes = change_name(
                        dict(guide.override_aes), old_aes_present, new_aes
                    )

            # Fallback palette path — ggplot2 4.0.0+ may set scale.palette to None
            # at construction time. R's `use_fallback_palette` instantiates a
            # dummy plot to recover the default palette.
            if getattr(scale, "palette", "missing") is None:
                scale = use_fallback_palette(scale, original_aes)

    set_protected(scale, original_aes)
    return scale


def bump_aes_scales(scales: list, original_aes: str, new_aes: str) -> list:
    """Apply :func:`bump_aes_scale` to every scale in *scales*."""
    return [bump_aes_scale(s, original_aes, new_aes) for s in scales]


def use_fallback_palette(scale: Any, original_aes: str, theme: Any = None) -> Any:
    """Reconstruct a missing palette by routing through a dummy plot.

    R counterpart: ``use_fallback_palette`` in ``R/bump-aes-scales.R``.

    Strategy: instantiate a fake ``ggplot()`` with a fake scale targeting
    *original_aes*, ask the resulting ScalesList to compute the palette,
    then clone the original scale with that palette installed.
    """
    if theme is None:
        theme = _gg.theme_get()

    dummy_scale = _gg.ggproto(None, scale, aesthetics=[original_aes])
    dummy_plot = _gg.ggplot() + dummy_scale
    scales_list = dummy_plot.scales

    set_palettes = getattr(scales_list, "set_palettes", None)
    if not callable(set_palettes):
        # Misconstructed scale prior to ggplot2 4.0.0 — nothing to do.
        return scale

    set_palettes(theme)

    matched = scales_list.get_scales(original_aes) if hasattr(scales_list, "get_scales") else None
    palette = getattr(matched, "palette", None) if matched is not None else None

    return _gg.ggproto(None, scale, palette=palette)


# ---------------------------------------------------------------------------
# Labels & guides
# ---------------------------------------------------------------------------


def bump_aes_labels(labels: Any, original_aes: str, new_aes: str, plot: Any | None = None) -> Any:
    """Rewrite ``plot.labels[original_aes]`` to ``plot.labels[new_aes]``.

    R counterpart: ``bump_aes_labels`` in ``R/bump-aes-labels.R``.

    The protect marker is stored on *plot* (parameter), not on the label
    string itself (per ggnewscale porting contract §3 — Python strings
    have no per-instance attribute slot). If *plot* is ``None`` (e.g. in
    direct unit tests), the marker is dropped.
    """
    if labels is None:
        return labels

    # Per-plot protected-labels set. GGPlot's ``__getattr__`` raises on
    # underscore-prefixed names and ``__setattr__`` routes them into
    # ``_meta`` — bypass both via ``object.__{get,set}attr__``.
    plot_marker_attr = "_ggnewscale_renamed_labels"
    if plot is not None:
        try:
            plot_marker = object.__getattribute__(plot, plot_marker_attr)
            if not isinstance(plot_marker, set):
                plot_marker = set(plot_marker)
        except AttributeError:
            plot_marker = set()
    else:
        plot_marker = set()

    out_type = type(labels)
    new_labels = dict(labels)

    if original_aes in new_labels and original_aes not in plot_marker:
        new_labels[new_aes] = new_labels.pop(original_aes)
        plot_marker = plot_marker | {original_aes}

    if plot is not None:
        object.__setattr__(plot, plot_marker_attr, plot_marker)

    if out_type is dict:
        return new_labels
    try:
        return out_type(new_labels)  # type: ignore[call-arg]
    except TypeError:
        return out_type(**new_labels)  # type: ignore[call-arg]


def bump_aes_guides(guides: Any, original_aes: str, new_aes: str) -> Any:
    """Rewrite a guides container so ``original_aes`` key becomes ``new_aes``.

    R counterpart: ``bump_aes_guides`` in ``R/bump-aes-guides.R``.

    ``guides`` is typically the dict ``plot.guides.guides`` from
    ggplot2_py, or any name->Guide mapping. Already-protected guides are
    skipped.
    """
    if guides is None:
        return guides

    out_type = type(guides)
    new_guides = dict(guides)

    if original_aes in new_guides:
        guide = new_guides[original_aes]
        if not is_protected(guide, original_aes):
            del new_guides[original_aes]

            # union(guide$available_aes, new_aes), preserving order.
            avail = _safe_aes_slot(guide, "available_aes")
            if isinstance(avail, (list, tuple)):
                new_avail = list(avail)
                if new_aes not in new_avail:
                    new_avail.append(new_aes)
                if isinstance(avail, tuple):
                    new_avail_typed: Any = tuple(new_avail)
                else:
                    new_avail_typed = new_avail
                guide.available_aes = new_avail_typed
            else:
                guide.available_aes = [new_aes]

            set_protected(guide, original_aes)
            new_guides[new_aes] = guide

    if out_type is dict:
        return new_guides
    try:
        return out_type(new_guides)  # type: ignore[call-arg]
    except TypeError:
        return out_type(**new_guides)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Helpers (private to this module)
# ---------------------------------------------------------------------------


def _rename_columns(data: Any, mapping: dict) -> Any:
    """Rename DataFrame columns or dict keys, dropping colliding targets first.

    Mirrors R ``colnames(data)[colnames(data) == new_aes] <- original_aes``
    (R/bump-aes-layers.R:55): in R the renamed-from value wins when
    ``data$<target>`` is later read. Python dicts can't hold duplicates,
    so the colliding target must be removed before the rename.
    """
    if data is None:
        return data
    if hasattr(data, "rename"):
        existing = set(data.columns)
        collisions = [v for k, v in mapping.items()
                      if k != v and k in existing and v in existing]
        if collisions:
            data = data.drop(columns=collisions)
        return data.rename(columns=mapping)
    if isinstance(data, dict):
        out = dict(data)
        for src, dst in mapping.items():
            if src == dst or src not in out:
                continue
            out[dst] = out.pop(src)
        return out
    return data


def _safe_default_aes(obj: Any) -> dict:
    val = getattr(obj, "default_aes", None)
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    # Mapping subclass already covered. Otherwise coerce.
    return dict(val)


def _safe_aes_slot(obj: Any, name: str) -> Any:
    """Return ``obj.<name>`` if present, else a sensible empty default."""
    if not hasattr(obj, name):
        return ()
    val = getattr(obj, name)
    if val is None:
        return ()
    return val


def _resolve_guide_constructor(name: str) -> Any:
    """Return the callable ``guide_<name>`` from ggplot2_py, or ``None``."""
    candidate = getattr(_gg, f"guide_{name}", None)
    return candidate if callable(candidate) else None


def _is_no_guide(guide: Any) -> bool:
    """True iff the scale's guide indicates "no legend" (R: scale$guide == 'none')."""
    if isinstance(guide, str):
        return guide == "none"
    if guide is False:
        return True
    GuideNone = getattr(_gg, "GuideNone", None)
    if GuideNone is not None:
        try:
            if isinstance(guide, GuideNone):
                return True
        except TypeError:
            pass
    if type(guide).__name__ == "GuideNone":
        return True
    return False


def _is_guide_proto(obj: Any) -> bool:
    Guide = getattr(_gg, "Guide", None)
    if Guide is None:
        return False
    try:
        return isinstance(obj, Guide)
    except TypeError:
        return False


def _mapping_like(template: Any, new_data: dict) -> Any:
    """Return *new_data* coerced to the same type as *template* (a ``Mapping``)."""
    if template is None:
        return new_data
    cls = type(template)
    if cls is dict:
        return new_data
    try:
        return cls(new_data)  # type: ignore[call-arg]
    except TypeError:
        return cls(**new_data)  # type: ignore[call-arg]


def _copy_extra_attrs(src: Any, dst: Any) -> None:
    """Copy custom Python attributes from *src* to *dst* without overwriting existing ones.

    Mirrors R's ``attributes(new_layer)[names(attributes_replace)] <- attributes_replace``
    pattern used in ``bump_aes_layer`` to preserve user-set attributes.
    """
    src_dict = getattr(src, "__dict__", None)
    dst_dict = getattr(dst, "__dict__", None)
    if src_dict is None or dst_dict is None:
        return

    # Slots already known to be ggproto state — copying these can corrupt the
    # clone-chain (we'd shadow the parent linkage). Skip standard ggproto bookkeeping.
    _ggproto_internal = {"_super_inst", "_class_name"}

    for k, v in src_dict.items():
        if k in _ggproto_internal:
            continue
        if k in dst_dict:
            continue
        # Use a shallow copy so the destination owns its own state where possible.
        try:
            dst_dict[k] = copy.copy(v)
        except (TypeError, copy.Error):
            dst_dict[k] = v
