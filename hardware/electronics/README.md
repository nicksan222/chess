# Electronics

Python is the source of truth for the revision-B electronics design.
[Schemdraw](https://schemdraw.readthedocs.io/en/stable/) draws every project,
and the placed symbols are counted into a bill of materials. There is no KiCad
project.

Revision B is a single board with no microcontroller on it. A Raspberry Pi
Zero 2 W reads 64 reed switches through four I2C expanders and shifts the LED
frame out over SPI, so the whole product is one Rust binary and there is no
firmware to write. The design is constrained to be reviewable by someone who is
not an electrical engineer and assemblable by hand: two IC part numbers, both
socketed, and nothing surface-mount except the LEDs. See
[`projects/board/README.md`](projects/board/README.md) for the reasoning.

Regenerate everything from the repository root with:

```sh
./tools/electronics
```

## Layout

Generated artefacts live in `generated/`; everything that produces them lives
in a subdirectory beside it.

```
generated/    drawings and the bill of materials
components/   one physical part per module
blocks/       reusable groups of components
core/         canvas, net names, bill of materials
projects/     one directory per sheet, each with generate.py
tests/
prototype/    build notes from physical prototypes, not source
```

`generated/` holds `<project>.svg`, `<project>.png` and `bom.md`. Never edit
anything in there; rerun the build instead. `hardware/cad` has the same shape.

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
    package="axial 5 mm",
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
100. Lower numbers run first.

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

## What the tests enforce

Beyond drawing correctly, the suite guards the design's constraints, so a change
that quietly breaks one fails the build:

- every square maps to exactly one expander pin, with no collisions
- every button lands on its own Broadcom line
- the LED chain is continuous for clock and data, and its 63 links stay
  electrically separate rather than shorting into one net
- the level buffer's spare channels are held disabled with their inputs tied off
- nothing surface-mount is placed except the LEDs
- the purchase list stays short enough to review

Revision B remains a physically unvalidated prototype. The open question is reed
sensitivity: a flat-lying reed under a vertical piece magnet couples through the
field's fringe, so build the single-square test in `prototype/` before ordering
a full board.
