# ggnewscale-python

Python port of the R [ggnewscale](https://eliocamp.github.io/ggnewscale/)
package (version 0.5.2.9000), licensed GPL-3.

> *Multiple fill and colour scales in
> [ggplot2_py](https://github.com/biobabel/ggplot2-python).*

## Installation

```bash
pip install -e ".[dev]"
```

`ggnewscale-python` requires
[`ggplot2-python`](https://github.com/biobabel/ggplot2-python) as its
plotting back-end. The R `ggnewscale` package is **not** required at
runtime (only by the porting / validation test suite).

## Quick start

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

(
    gg.ggplot(df, gg.aes("x", "y"))
    + gg.geom_point(gg.aes(color="category"), size=6)
    + gg.scale_color_brewer(palette="Set1")
    + new_scale_color()                            # open a fresh colour slot
    + gg.geom_point(gg.aes(color="magnitude"), size=2)
    + gg.scale_color_viridis_c()
)
```

## Public API

The Python public API mirrors the R `ggnewscale` package 1:1:

| Python | R equivalent |
|---|---|
| `new_scale(aes)` | `new_scale(aes)` |
| `new_scale_color()` | `new_scale_color()` |
| `new_scale_colour()` | `new_scale_colour()` |
| `new_scale_fill()` | `new_scale_fill()` |
| `rename_aes(**kwargs)` | `rename_aes(...)` |
| `clear_aes()` | `clear_aes()` |

See [the docs](docs/index.md) for the full quickstart and API reference.

## Building the docs

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Running the tests

```bash
pip install -e ".[dev]"
pytest -v
```

The volcano render-parity test (`test_volcano_smoke.py`) requires
`Rscript` at `/home/groups/xiaojie/nianping/Conda_Files/envs/ggrepel-dev/bin/Rscript`;
adjust `_RSCRIPT_ENV` in that file for your environment.

## License

GPL-3.0-only (matches R `ggnewscale`).
