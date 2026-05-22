# API Reference

The Python package exposes the same six functions as R `ggnewscale`, plus
three marker dataclasses for advanced extensions.

## Public functions

::: ggnewscale.new_scale
::: ggnewscale.new_scale_color
::: ggnewscale.new_scale_colour
::: ggnewscale.new_scale_fill
::: ggnewscale.rename_aes
::: ggnewscale.clear_aes

## Marker classes

The marker dataclasses are returned by the public functions; they are
dispatched on at `+` time via
[`ggplot2_py.plot.update_ggplot`](https://github.com/biobabel/ggplot2-python).
Most users do not interact with them directly.

::: ggnewscale.NewAes
::: ggnewscale.RenameNext
::: ggnewscale.ClearAes

## Extension hooks

Define a custom `scale_<aes>_<type>` at your module's top level and it
will be picked up automatically (mirroring R's `as.environment(-1)`
globalenv lookup). If your custom constructor lives in a class, factory,
or other non-module-global scope, use:

::: ggnewscale.register_constructor
::: ggnewscale.unregister_constructor
