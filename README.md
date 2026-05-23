# ggnewscale-python

[![PyPI](https://img.shields.io/pypi/v/ggnewscale-python)](https://pypi.org/project/ggnewscale-python/)

Python port of the R [ggnewscale](https://eliocamp.github.io/ggnewscale/) package.


## Installation

```bash
pip install ggnewscale-python
```

## Tutorial

See [`tutorials/ggnewscale_overview.ipynb`](tutorials/ggnewscale_overview.ipynb)
for a guided tour of every public API entry point with side-by-side
renderings.

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

