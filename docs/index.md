# ggnewscale-python

Python port of the R [ggnewscale](https://eliocamp.github.io/ggnewscale/)
package (Elio Campitelli, GPL-3).

> *Multiple fill and colour scales in [ggplot2_py](https://github.com/biobabel/ggplot2-python).*

## Why?

`ggplot2` (and `ggplot2_py`) only ever uses **one** scale per aesthetic in a
plot. If you have a contour layer mapping `colour` to a numeric variable and
*also* want a point layer mapping `colour` to a different categorical
variable, the second `scale_colour_*()` you add would silently replace the
first. `ggnewscale` solves this by renaming the aesthetic of all
previously-added layers / scales / guides to a unique mangled name
(`colour_ggnewscale_1`, `colour_ggnewscale_2`, ...) so subsequent
`+ scale_colour_*()` calls bind to a fresh slot.

## Installation

```bash
pip install -e .
```

`ggnewscale-python` requires the [`ggplot2-python`](https://github.com/biobabel/ggplot2-python)
package as its plotting back-end. The R `ggnewscale` package is **not**
required at runtime (it is only used by the porting / validation test
suite).

## Quickstart

```python
import pandas as pd
import ggplot2_py as gg
from ggnewscale import new_scale_color

df = pd.DataFrame({
    "x": [1, 2, 3, 4, 5],
    "y": [3, 1, 4, 1, 5],
    "category": ["A", "B", "A", "B", "A"],
    "magnitude": [10.0, 20.0, 30.0, 40.0, 50.0],
})

p = (
    gg.ggplot(df, gg.aes("x", "y"))
    + gg.geom_point(gg.aes(color="category"), size=6)
    + gg.scale_color_brewer(palette="Set1")
    + new_scale_color()                            # open a fresh colour slot
    + gg.geom_point(gg.aes(color="magnitude"), size=2)
    + gg.scale_color_viridis_c()
)
p
```

## The volcano example

This is the original example from `ggnewscale`'s README. Two colour scales —
one for elevation contours, one for point measurements — coexist on the
same canvas.

```python
import numpy as np
import pandas as pd
import ggplot2_py as gg
from ggnewscale import new_scale_color

volcano = np.loadtxt("volcano.csv", delimiter=",")  # R datasets::volcano
ny, nx = volcano.shape
topography = pd.DataFrame({
    "x": np.tile(np.arange(1, ny + 1), nx),
    "y": np.repeat(np.arange(1, nx + 1), ny),
    "z": volcano.flatten(order="F"),
})

rng = np.random.default_rng(0)
measurements = pd.DataFrame({
    "x": rng.uniform(1, 80, 30),
    "y": rng.uniform(1, 60, 30),
    "thing": rng.standard_normal(30),
})

(
    gg.ggplot(mapping=gg.aes("x", "y"))
    + gg.geom_contour(
        data=topography,
        mapping=gg.aes(z="z", color=gg.after_stat("level")),
    )
    + gg.scale_color_viridis_c(option="D")
    + new_scale_color()
    + gg.geom_point(data=measurements, size=3, mapping=gg.aes(color="thing"))
    + gg.scale_color_viridis_c(option="A")
)
```

## Public API

The six R-API functions are re-exported at the top level:

- [`new_scale`](api.md) — open a new scale slot for any aesthetic.
- `new_scale_color` / `new_scale_colour` — shorthand for `new_scale("colour")`.
- `new_scale_fill` — shorthand for `new_scale("fill")`.
- [`rename_aes`](api.md) — one-shot rename of an aesthetic on the next layer.
- [`clear_aes`](api.md) — tear down a `rename_aes` rename.

See the [API Reference](api.md) for full signatures and docstrings.

## Compatibility

| Component | Version |
|---|---|
| Python | >= 3.10 |
| `ggplot2_py` | >= 4.0.2 |
| Mirrors R `ggnewscale` version | 0.5.2.9000 |

## License

GPL-3.0-only (matches R `ggnewscale`).
