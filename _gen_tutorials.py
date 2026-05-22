"""Stage tutorials/*.ipynb into docs/tutorials/ before each mkdocs build.

The canonical <r_name>-python layout keeps tutorial notebooks at
tutorials/ (the distribution artifact listed in pyproject.toml) while
mkdocs builds from docs/. This pre-build hook bridges the two: it
symlinks tutorials/*.ipynb into docs/tutorials/ so mkdocs-jupyter can
render them in place without a second copy on disk.

docs/tutorials/ is declared in .gitignore and is managed exclusively by
this hook -- it is wiped and regenerated on every build so renames and
deletions in the source tree propagate.

Filesystem-driven, not flag-driven: when tutorials/ is missing or holds
no .ipynb files, this hook is a no-op. Safe to keep registered in
packages ported without tutorials.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def _stage_tutorials(config) -> None:
    docs_dir = Path(config["docs_dir"])
    src = docs_dir.parent / "tutorials"
    dest = docs_dir / "tutorials"

    if dest.is_symlink() or dest.exists():
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)

    if not src.is_dir():
        return

    notebooks = sorted(
        p for p in src.iterdir()
        if p.is_file() and p.suffix == ".ipynb"
    )
    if not notebooks:
        return

    dest.mkdir(parents=True, exist_ok=True)
    for nb in notebooks:
        link = dest / nb.name
        # Relative symlink keeps the docs tree portable.
        link.symlink_to(os.path.relpath(nb, link.parent))


def on_pre_build(config, **kwargs) -> None:
    _stage_tutorials(config)


def on_serve(server, config, builder, **kwargs):
    src = Path(config["docs_dir"]).parent / "tutorials"
    if src.is_dir():
        server.watch(str(src))
    return server
