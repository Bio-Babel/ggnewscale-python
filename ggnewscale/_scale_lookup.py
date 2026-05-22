"""Scale lookup environment plumbing.

R reference: ``R/rename-aes.R``::``find_global``, ``find_scale``, ``assing_scales``
(note the typo in the original R name; we use the corrected spelling
``assign_scales`` on the Python side).

These helpers pre-register ``scale_<new_aes>_<type>`` factories on the plot's
``plot_env`` so that ggplot2_py's ``find_scale(aes, x, env=plot.plot_env)``
returns a sensible default scale when it encounters a mangled aesthetic name
(e.g. ``"colour_ggnewscale_1"``) introduced by ggnewscale's bumping.

Lookup order mirrors R's ``find_global(name, env=as.environment(-1), ...)``:

1. **Caller environment** — a dict-like ``env`` mapping, typically the user's
   ``f_globals`` captured at the entry point of ``ggplot_add.new_aes``.
   In R this is ``as.environment(-1)``, which evaluates to the user's
   global environment (search list position 1). A custom ``scale_topo_continuous``
   defined in the user's script is found via this branch in both R and
   Python.
2. **`ggplot2_py` namespace** — the package-level functions for built-in
   scales and guides.

See also: the user-facing registration hook :func:`register_constructor`
which lets advanced users add ``scale_*`` / ``guide_*`` factories to a
process-wide registry consulted in addition to (1) and (2).
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

import ggplot2_py as _gg

__all__: list[str] = []

# R: c("continuous", "discrete", "time", "ordinal", "datetime"). We mirror the
# full list — ggplot2_py uses the same names for the ones it actually has
# (continuous/discrete/datetime/ordinal). ``time`` is registered for R parity
# but will simply never be looked up because ggplot2_py's ``scale_type`` does
# not return it.
_SCALE_TYPES: tuple[str, ...] = ("continuous", "discrete", "time", "ordinal", "datetime")


# ---------------------------------------------------------------------------
# Optional user-side registration hook (Pythonic complement to env walking)
# ---------------------------------------------------------------------------

_USER_REGISTRY: dict[str, Callable[..., Any]] = {}


def register_constructor(name: str, fn: Callable[..., Any]) -> None:
    """Register a custom ``scale_*`` or ``guide_*`` constructor with ggnewscale.

    R counterpart: in R, defining ``scale_foo_continuous`` in the user's
    global environment is enough — ``find_global`` walks the search path
    and picks it up. Python has no such implicit chain, so the recommended
    extension hook is this explicit registration.

    The registered constructors are consulted *in addition to* the
    caller-frame globals walked by ``find_global`` and the ``ggplot2_py``
    package namespace.

    Parameters
    ----------
    name : str
        Symbol name, e.g. ``"scale_topo_continuous"``.
    fn : callable
        The factory function.

    Examples
    --------
    >>> def scale_topo_continuous(**kw):
    ...     return ggplot2_py.scale_colour_continuous(**kw)
    >>> register_constructor("scale_topo_continuous", scale_topo_continuous)
    """
    _USER_REGISTRY[name] = fn


def unregister_constructor(name: str) -> None:
    """Remove a previously registered constructor (does nothing if absent)."""
    _USER_REGISTRY.pop(name, None)


# ---------------------------------------------------------------------------
# Caller-frame globals capture
# ---------------------------------------------------------------------------


_INTERNAL_PACKAGE_NAMES: frozenset[str] = frozenset({"ggnewscale", "ggplot2_py"})


def _is_internal_frame(frame: Any) -> bool:
    """True iff *frame* lives in ggnewscale, ggplot2_py, the stdlib, or site-packages.

    We skip stdlib (e.g. ``functools.wrapper`` from ``singledispatch``) and
    every other site-packages module because none of those are the user's
    own scale/guide-defining module — they're routing layers between the
    user's ``+`` call and our handler.
    """
    parts = Path(frame.f_code.co_filename).resolve().parts
    if any(name in parts for name in _INTERNAL_PACKAGE_NAMES):
        return True
    # Skip Python stdlib + any installed package (these are never the
    # user's own code in any sane setup).
    if "site-packages" in parts:
        return True
    # CPython's stdlib usually lives under .../lib/pythonX.Y/ — and never
    # contains 'site-packages' as a *direct* ancestor of the file but does
    # contain '/lib/pythonX.Y/' or '/lib/python3' in the path.
    joined = "/".join(parts)
    if "/lib/python3" in joined or "/lib/python2" in joined:
        # But allow site-packages-inside-lib (already handled above).
        return True
    return False


def capture_user_globals() -> Optional[Mapping[str, Any]]:
    """Walk the call stack to the first user-code frame.

    A "user-code frame" is one whose file is **not** in ggnewscale,
    ggplot2_py, the Python stdlib, or any ``site-packages`` directory.
    The matching frame's ``f_globals`` is returned so :func:`find_global`
    can locate user-defined ``scale_*`` / ``guide_*`` constructors declared
    in the user's module.

    This mirrors R's ``as.environment(-1)`` semantics: R returns the
    globalenv() (search-list position 1) which contains user-defined
    helpers. Walking past internal layers is the Python analogue.

    Returns
    -------
    Mapping[str, Any] or None
        The first user frame's ``f_globals`` if found, else ``None``.
    """
    frame: Any = sys._getframe(1)
    while frame is not None:
        if not _is_internal_frame(frame):
            return frame.f_globals
        frame = frame.f_back
    return None


# ---------------------------------------------------------------------------
# Core lookup
# ---------------------------------------------------------------------------


def find_global(
    name: str, env: Optional[Mapping[str, Any]] = None
) -> Optional[Callable[..., Any]]:
    """Look up *name* as a callable.

    R counterpart::

        find_global <- function(name, env, mode = "any") {
          if (exists(name, envir = env, mode = mode)) return(get(...))
          nsenv <- asNamespace("ggplot2")
          if (exists(name, envir = nsenv, mode = mode)) return(get(...))
          return(NULL)
        }

    Lookup order:

    1. The user-side process-wide :data:`_USER_REGISTRY` (extension hook).
    2. The caller-frame globals *env* (R's ``as.environment(-1)`` analogue —
       lets users define e.g. ``scale_foo_continuous`` at module level).
    3. The ``ggplot2_py`` package namespace.

    ``ggplot2_py`` defines several names (``guide_legend``, ``guide_colourbar``,
    ``guide_colorbar``) both as top-level functions *and* as submodules.
    Depending on import order ``getattr(ggplot2_py, name)`` may return the
    submodule — we peel through the submodule to find the callable when
    that happens.

    Parameters
    ----------
    name : str
        Symbol name (e.g. ``"scale_colour_continuous"``, ``"guide_legend"``).
    env : Mapping[str, Any], optional
        User-side lookup table. Typically a frame's ``f_globals``.

    Returns
    -------
    callable or None
    """
    # 1. Explicit registration hook.
    if name in _USER_REGISTRY:
        return _USER_REGISTRY[name]

    # 2. Caller environment (user globals).
    if env is not None and name in env:
        candidate = env[name]
        if callable(candidate):
            return candidate

    # 3. ggplot2_py namespace (with submodule-vs-function disambiguation).
    fn = getattr(_gg, name, None)
    if callable(fn):
        return fn
    if fn is not None:
        inner = getattr(fn, name, None)
        if callable(inner):
            return inner
    return None


def find_scale(
    new_aes: str,
    original_aes: str,
    type_: str,
    env: Optional[Mapping[str, Any]] = None,
) -> Optional[Callable[..., Any]]:
    """Build a factory that produces ``scale_<original_aes>_<type_>`` retargeted to *new_aes*.

    R counterpart: ``find_scale(new_aes, original_aes, type)`` in
    ``R/rename-aes.R``.

    The returned callable takes no arguments (or arbitrary ``**kwargs``,
    matching R's ``function(...)`` signature) and produces a
    ``ggplot2_py`` scale with:

    - ``aesthetics = new_aes`` (so the new ScalesList lookup matches the
      mangled name);
    - ``guide`` configured for ``new_aes`` (built either via the
      constructor's ``available_aes`` argument when supported, or via a
      bare ``guide_*()`` call).

    Returns ``None`` if no ``scale_<original_aes>_<type_>`` constructor exists.

    Parameters
    ----------
    new_aes : str
        Mangled aesthetic name (e.g. ``"colour_ggnewscale_1"``).
    original_aes : str
        Standardised original aesthetic name (e.g. ``"colour"``).
    type_ : str
        One of ``_SCALE_TYPES``.
    env : Mapping[str, Any], optional
        Lookup env passed through to :func:`find_global`.

    Returns
    -------
    callable or None
    """
    og_name = f"scale_{original_aes}_{type_}"
    og_fun = find_global(og_name, env=env)
    if og_fun is None:
        return None

    # Build a default scale to discover its preferred guide.
    og_guide_marker = og_fun().guide

    if isinstance(og_guide_marker, str):
        og_guide_fun = find_global(f"guide_{og_guide_marker}", env=env)
    else:
        og_guide_fun = og_guide_marker  # already a Guide ggproto factory or instance

    if og_guide_fun is None:
        og_guide: Any = None
    elif (
        inspect.isfunction(og_guide_fun)
        or inspect.isbuiltin(og_guide_fun)
        or (callable(og_guide_fun) and not _looks_like_guide_instance(og_guide_fun))
    ):
        sig_params = _safe_signature_params(og_guide_fun)
        if sig_params is not None and "available_aes" in sig_params:
            og_guide = og_guide_fun(available_aes=[new_aes])
        else:
            og_guide = og_guide_fun()
    else:
        og_guide = og_guide_fun

    def _factory(*args: Any, **kwargs: Any) -> Any:
        # Mirrors R: function(...) og_fun(..., aesthetics = new_aes, guide = og_guide)
        kwargs.setdefault("aesthetics", new_aes)
        if og_guide is not None:
            kwargs.setdefault("guide", og_guide)
        return og_fun(*args, **kwargs)

    return _factory


def _looks_like_guide_instance(obj: Any) -> bool:
    """Heuristic: is *obj* already an instantiated Guide (rather than its constructor)?"""
    Guide = getattr(_gg, "Guide", None)
    if Guide is None:
        return False
    try:
        return isinstance(obj, Guide)
    except TypeError:
        return False


def _safe_signature_params(fn: Callable[..., Any]) -> Optional[dict]:
    """Like ``inspect.signature(fn).parameters`` but returns ``None`` on failure."""
    try:
        return inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return None


def assign_scales(
    new_aes: str,
    original_aes: str,
    plot: Any,
    env: Optional[Mapping[str, Any]] = None,
) -> Any:
    """Pre-register ``scale_<new_aes>_<type>`` factories on *plot*'s ``plot_env``.

    R counterpart: ``assing_scales`` (the R-side name carries a typo;
    the Python spelling is corrected as ``assign_scales``).

    For each scale type in :data:`_SCALE_TYPES` (``continuous``, ``discrete``,
    ``time``, ``ordinal``, ``datetime``), a factory is registered such that
    when ``ggplot2_py.scales.find_scale`` later resolves an unknown
    ``scale_<new_aes>_<type>``, it gets a scale targeting the renamed
    aesthetic with an appropriate guide.

    Parameters
    ----------
    new_aes : str
        Mangled aesthetic name.
    original_aes : str
        Standardised original aesthetic name.
    plot : ggplot2_py.GGPlot
        The plot whose ``plot_env`` is updated.
    env : Mapping[str, Any], optional
        User-side lookup env. If ``None``, the caller's frame globals are
        captured by walking past ggnewscale and ggplot2_py frames —
        mirroring R's ``as.environment(-1)`` for the user's globalenv.

    Returns
    -------
    ggplot2_py.GGPlot
        The same *plot* (mutated in place).
    """
    if env is None:
        env = capture_user_globals()

    layer: dict[str, Callable[..., Any]] = {}
    for type_ in _SCALE_TYPES:
        name = f"scale_{new_aes}_{type_}"
        fn = find_scale(new_aes, original_aes, type_, env=env)
        if fn is not None:
            layer[name] = fn
    if layer:
        plot.plot_env.push(layer)
    return plot
