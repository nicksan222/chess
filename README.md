# Chess ♟️

Chess is an open-source smart chessboard you can build, modify, and play on.
Each square senses a magnetic piece and has its own RGB light, allowing the board
to follow a physical game, highlight moves, and provide feedback. A Raspberry Pi
Zero 2 W runs the whole thing in Rust.

<div align="center">
  <a href="hardware/cad/generated/board-assembly-finished.png">
    <img src="hardware/cad/generated/board-assembly-finished.png" width="62%" alt="Finished smart chessboard render">
  </a>
  <a href="hardware/cad/generated/board-assembly-open.png">
    <img src="hardware/cad/generated/board-assembly-open.png" width="31%" alt="Board with the tile plate lifted clear">
  </a>
  <br>
  <sub>The finished board—and the same board with its plate lifted off. See the <a href="hardware/cad/">Blender CAD sources</a>.</sub>
</div>

## What makes it buildable

The design is deliberately constrained so that someone who is not an electrical
engineer can review it and assemble it by hand at a kitchen table:

- **One PCB**, 320 x 360 mm, carrying all 64 sensors, all 64 LEDs and the control
  panel. No wiring harness.
- **Two IC part numbers**, both through-hole in sockets, so no chip ever sees a
  soldering iron. About eighteen things to buy in total.
- **Two printed parts**: a case and a single plate with the checkerboard engraved
  into it. The previous revision needed 129 prints to cover a board.
- **No firmware.** The board has no microcontroller, so there is no second
  toolchain, no cross-compilation target and no flashing step — just one Linux
  binary on the Pi.

That last point is only possible because of two component choices: every reed
switch gets its own pin on an I2C expander instead of being scanned as a matrix,
and the LEDs are SK9822, which carry a clock line and so have no timing
requirement a non-real-time host could violate.
[`docs/hardware.md`](docs/hardware.md) explains both.

## Repository

The repository contains the software, the design contract, the board layout and the
printable CAD needed to build the board. Fabrication output is generated from
reviewed Python and JSON sources, with no EDA application in the loop. Run `make gen` to regenerate everything, or see
[`docs/development.md`](docs/development.md) for the complete development
workflow. [`docs/assembly.md`](docs/assembly.md) covers what to order and the
order to solder it in.

## Status

The mechanical design and revision-B PCB sources are ready for review, and the
board layout generates real Gerbers. Nothing has been physically built yet.

Two things stand between this and a working board:

- **The layout is partly routed.** 127 of 214 connections are done — the LED
  chain and ground — and the reed sense lines, buses and 5 V distribution are
  not. The fabrication package is deliberately withheld until every net is
  routed, because a fab cannot tell an unrouted board from a finished one.
  `hardware/pcb/generated/routing.md` is the running score.
- **Reed sensitivity is unproven.** The reeds lie flat under a vertical piece
  magnet, so they couple through the field's fringe rather than head-on. Test one
  square on prototyping board before ordering a full one.

The host application is not written. The board model that turns sensor bytes into
chess squares is, and so is the chess engine behind it.
