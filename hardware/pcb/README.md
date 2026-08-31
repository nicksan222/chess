# Fabrication

Python is the source of truth for the board's artwork.
[Gerbonara](https://gerbolyze.gitlab.io/gerbonara) writes the Gerber and Excellon
files directly, so this domain needs no EDA application and there is no KiCad
project anywhere in the repository.

Regenerate everything from the repository root with:

```sh
./tools/pcb
```

`design/netlist.json` is the reviewed electrical connectivity contract. The
layout reads it directly; there is no separate design contract domain that can drift
from the PCB sent to fabrication.

## Read this before ordering anything

**The board is not finished.** `generated/routing.md` is the honest state of it.
At the time of writing, 127 of 214 connections are routed: the LED chain and
ground are done, and the 64 reed sense lines, the buses and 5 V distribution are
not.

The fabrication package is **withheld** until every connection is routed. That
gate exists because Gerber output is valid long before a board would work, and a
fab cannot tell the difference — it will happily manufacture an unrouted board
and ship it. So `board-pcbway.zip` only appears when the layout is actually
complete.

## What this domain does and does not guarantee

It does:

- place all 228 parts on real coordinates taken from the mechanical design, so
  the copper cannot drift from the plastic;
- check nothing overlaps and nothing hangs off the board;
- keep every dimension inside the fab's stated capability, with a wide margin;
- clear the ground pour away from every pad that is not on ground;
- verify that each net the connectivity contract declares is joined in copper.

It does **not**:

- run a design-rule check over finished geometry. It reasons about endpoints, so
  it will not notice a trace crossing another net, or two traces too close
  together. It answers "is this net joined up", not "is this board correct".
- compute thermal reliefs, or teardrops, or anything else a mature CAD tool
  would.

So: check the fab's own preview and DRC report before paying. That is not
optional here.

## Layout

```
design/       reviewed connectivity contract and assembly manifest
generated/    gerber stack, previews, routing report, upload package
core/         rules, sources, placement, routing, layers, connectivity
footprints/   one physical package per module
projects/     one directory per board, each with generate.py
tests/
```

`core/rules.py` holds two sets of numbers: the manufacturer's stated capability,
which is not ours to choose, and the geometry this design uses, which is. It
refuses any choice outside the capability, so raising a limit cannot silently
produce an unmanufacturable board.

`core/sources.py` loads dimensions and wiring from `hardware/shared` and reads
the local design connectivity. Tool-specific code remains in this domain.

## Adding a footprint

Add a module to `footprints/` binding a `Footprint` to an UPPER_CASE name. The
catalog discovers it and indexes it by its `package` string — the same string the
design contract records — so nothing else needs editing.

Derive the courtyard with `courtyard_for()` rather than writing one out. A
courtyard smaller than its own pads is a bug the tests will catch, but not
writing it by hand is better than catching it.

Pad numbers are datasheet pin numbers so they match the connectivity contract.
Where a package has more pads than the logical component has pins — a tactile switch's four legs
are two shorted pairs — suffix the extras with a letter: `2b` carries whatever
pin `2` carries.

## Coordinates

Placement uses the mechanical design's coordinates: the playing area centred on
the origin, the control strip in negative Y. The shift into the positive quadrant
Gerber expects happens once, in `core/layers.py`, so everything else thinks in the
same frame as the CAD.

## Previews

Open the SVGs in a browser. Gerbonara colours the layers with SVG filters, and
most command-line rasterisers ignore filters, which renders the traces white on
white and makes an entirely correct board look empty.
