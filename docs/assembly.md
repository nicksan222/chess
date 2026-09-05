# Assembly

## Before ordering

Build one DRV5032FC sensor, its 100 nF bypass capacitor, one SK9822, and one
TCA9554DWR at the final CAD stack height. Verify reliable operate and release with
both magnet poles, exercise a full eight-sensor bank while updating LEDs,
and record the result in `hardware/pcb/board/prototype/`.

Run `just --justfile hardware/pcb/justfile release` in the reproducible KiCad container. Fabrication output is
withheld unless tests, ERC, DRC, schematic parity, routing, and prototype evidence
all pass. Also review the fabricator's rendering before payment.

## What to order

`hardware/pcb/generated/bom.md` is generated from the approved exact-MPN catalog and
reviewed netlist. The Raspberry Pi Zero 2 W, SK9822 architecture, eight TCA9554DWRs,
and external 5 V supply remain part of the design.

You will also need the two printed parts, a chess set with a king base no larger
than 32 mm, and magnets for the pieces.

## Board notes

- Eight copper layers, 1.6 mm finished thickness, 320 x 360 mm.
- 0.31 mm signal traces, 1.5 mm input-power traces, and 0.30 mm clearance.
- Dedicated GND, +5 V, and +3.3 V planes; three internal signal layers.
- SMD assembly on the top side, with through-hole connectors and controls where
  their mechanical function warrants it.

## Suggested assembly order

1. Solder the 0603/0805 passives, Hall sensors, SOIC ICs, SMD fuse/TVS, test
   points, and SK9822 LEDs. Check orientation of every polarized or pin-1 part.
2. Inspect fine-pitch joints and verify that +5 V, +3.3 V, and GND are not
   shorted before fitting through-hole parts.
3. Fit the buttons, display and Pi sockets, barrel jack, rocker switch, and bulk
   electrolytic capacitor.
4. Clean and inspect the board, then perform current-limited first power-up.

## First power-up

1. Leave the Pi and display unplugged. Apply current-limited 5 V at the barrel
   jack and verify the protected +5 V rail.
2. Confirm +3.3 V is absent until the Pi is installed; it is supplied by the Pi
   header.
3. Power down, install the Pi, then verify TCA9554DWR addresses 0x20-0x27 and the
   display at 0x3C. Follow [polled register setup](host.md#reading-the-board);
   never configure a Hall input as an output. INT pin 13 is deliberately NC on
   every bank; no IRQ pull-up/testpoint is fitted.
4. Probe buffered LED clock/data and verify all 64 active-low Hall outputs with a
   magnet before mechanical assembly. Measure Hall release edges/noise and
   SDA/SCL rise times at the furthest banks during LED updates. Record real
   D-PROTOTYPE evidence, including final CAD spacing; generated checks alone
   do not qualify the weak pull-ups or bus timing.

Power the finished board from the barrel jack only; do not simultaneously feed
the Pi through micro-USB.
