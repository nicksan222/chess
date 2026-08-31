# Fabrication

## Purpose

Describe how the board's manufacturing files are produced, and be precise about
what that process guarantees.

## Gerbers without an EDA tool

`hardware/pcb` writes RS-274X Gerber and Excellon files directly, using
[Gerbonara](https://gerbolyze.gitlab.io/gerbonara). There is no KiCad project, no
schematic capture application, and no board file to open: the artwork is a
consequence of the schematic and the mechanical design, both of which are already
Python.

That is possible mainly because this board is unusually regular. Every one of the
64 cells sits on a 40 mm grid, and the coordinates already exist — the LED
positions are the ones the tile plate's diffuser pockets use, and the button
positions are the ones the case bezel drills. Placement is therefore derived, not
drawn, and the copper cannot drift away from the plastic.

## Two domains, joined by a file

The schematic publishes `hardware/electronics/generated/netlist.json`, and the
layout reads it. Deliberately a file and not an import: the fabrication toolchain
then needs Gerbonara and nothing else, the two domains stay independently
installable, and the contract between them is something a person can open.

The netlist publishes **complete connectivity**, not just named nets. A link drawn
as a plain wire carries no net name, and the LED chain uses one for every step
along a rank, so publishing only named nets would have hidden those connections
from the layout — which would then have produced a board with an unrouted LED
chain and no sign anything was wrong.

Run `./tools/electronics` before `./tools/pcb`. `./tools/check` and `make gen`
already do.

## The gate

An unrouted board produces perfectly valid Gerber files. A fab will accept them,
manufacture them and ship them, because valid and connected are different
properties and only one of them is visible in the file.

So the fabrication package is withheld until every connection the schematic
declares is realised in copper. `generated/routing.md` reports the state, grouped
into a work list. If `board-pcbway.zip` is missing, the board is not ready and
that is the gate working.

At the time of writing: 127 of 214 connections routed. The LED chain (126 links)
and ground are done. Outstanding are the 64 reed sense lines, the panel button
lines, the buses and 5 V distribution.

## What is verified, and what is not

Verified, by tests that run in CI:

- the chosen geometry is inside PCBWay's stated capability, with a margin of four
  times the process floor, and raising a limit past the capability is refused;
- every package the schematic places has a footprint, and every schematic pin has
  a pad;
- no two parts overlap and nothing hangs off the board;
- every LED, reed and button sits where the mechanical design put a pocket or a
  hole;
- the ground pour clears every pad that is not on ground — without which the
  pour would short the entire board;
- the written files read back as what was meant;
- every declared net is joined in copper.

**Not verified: there is no design-rule check over finished geometry.** The
connectivity analysis reasons about endpoints, so it will not notice a trace
crossing another net, or two traces closer than the clearance allows. It answers
"is this net joined up", not "is this board correct".

That is why the ordering advice is to upload, read the fab's own rendering and
DRC report, and only then pay. The gate here prevents shipping something
obviously incomplete; it does not replace a real DRC.

## Known simplifications

- The ground pour is a plain negative region. No thermal reliefs, so a
  hand-soldered joint on a ground pad will sink heat into the plane.
- Traces are orthogonal segments only, with right-angle corners rather than
  mitres. Irrelevant at these frequencies.
- Silkscreen text uses a small built-in stroke font covering A-H and 1-8, which
  is all the board writes.
- Board thickness, surface finish and copper weight are order-form choices, not
  encoded in the artwork.
