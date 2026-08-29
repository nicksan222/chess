# Electronics

Python is the source of truth for the revision-A electronics design.
[Schemdraw](https://schemdraw.readthedocs.io/en/stable/) draws every project,
and the placed symbols are counted into a bill of materials. There is no KiCad
project.

Regenerate everything from the repository root with:

```sh
make electronics
```

## Layout

Generated artefacts sit at the top of this directory; everything that produces
them lives in a subdirectory.

```
chessboard.svg / .png   generated drawing of the complete board
square.svg / .png       generated drawing of one square
bom.md                  generated bill of materials with quantities

components/             one physical part per module
blocks/                 reusable groups of components
core/                   canvas, net names, bill of materials
projects/               one directory per sheet, each with generate.py
tests/
```

Never edit the generated files; rerun the build instead.

## Adding a component

Add one module to `components/` that binds a `Component` to an UPPER_CASE
name:

```python
from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

INDUCTOR = Component(
    lib="L",
    value="10uH",
    description="Output filter inductor",
    package="1210",
    build=lambda: elm.Inductor().right(),
    pins=TWO_TERMINAL,
)
```

That is the whole job. The catalog discovers the module, so there is no import
list to update, and the bill of materials counts whatever the schematics place,
so `core/bom.py` never needs editing either.

Every part declares the same fields: `lib`, `value`, `description`, `package`,
a `build` callable returning a Schemdraw element, and a `pins` map from
datasheet pin number to Schemdraw anchor. Use `part` when the drawn value is a
net name rather than something orderable, as test points do.

## Adding a project

Add a directory under `projects/` with a `generate.py` exposing `assemble()`
and `build()`. The runner discovers it; so does the bill of materials. A
project may include a `generation-order` file containing a non-negative integer
when it depends on another project's output; projects without one default to
100. Run `./tools/electronics list` to inspect the execution order.

## Drawing scale

Schemdraw sizes geometry in drawing units but text in points, so `UNIT` and
`INCHES_PER_UNIT` in `core/canvas.py` decide how crowded a sheet looks.
Lowering `INCHES_PER_UNIT` shrinks the circuit while leaving every label the
same size, which is what makes a drawing look compressed. Keep the geometry
generous and the type small.

The board sheet is large, so the SVG is the zoomable master and the PNG is a
screenshot capped at `ELECTRONICS_PNG_MAX_PIXELS` (5000 px on the longest side)
to stay openable. `ELECTRONICS_PNG_DPI` sets the upper bound.

Each sheet gets a border, a lower-right title block, and one outlined section
per functional block. Sections measure their own contents, so an outline can
never drift out of step with a layout change.

The first run creates `.cache/electronics` and installs `requirements.txt`.
Revision A remains a physically unvalidated prototype; its validation gates are
documented instead of being represented as production results.
