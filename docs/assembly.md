# Assembly

## Purpose

Describe what to order and the order to solder it in.

## Before you spend anything

**Test one square first.** Reed sensitivity is the open question in this design:
the reeds lie flat under a vertically oriented piece magnet, so they couple
through the field's horizontal fringe rather than head-on. Build one reed, one
LED and one expander on a scrap of prototyping board, glue a magnet into a piece,
and confirm it triggers reliably at the height the plate puts it at. Record the
result in `hardware/pcb/prototype/`.

That costs a few pounds. Discovering an orientation problem after ordering five
320 x 360 mm boards does not.

**The layout is not finished.** `hardware/pcb` generates real Gerber and Excellon
files, but only part of the board is routed: the LED chain and ground are done,
and the reed sense lines, buses and 5 V distribution are not.

`./tools/pcb` withholds `board-pcbway.zip` until every net is routed, and
`hardware/pcb/generated/routing.md` says what is outstanding. If the zip is
missing, the board is not ready to order — that is the gate doing its job, not a
build failure.

**Check the fab's own DRC before paying.** This toolchain verifies that nets are
joined and that the geometry is inside PCBWay's stated capability. It does not
run a design-rule check over finished copper, so it cannot tell you that two
traces are too close together. Upload, look at the fab's rendering and DRC
report, and only then order.

## What to order

`hardware/pcb/design/bom.md` is the reviewed assembly manifest maintained with
the connectivity contract. The "To order" table is the shopping list, about
eighteen lines.

Two things are not on it because they are not electronics:

- The two printed parts, quoted from an **FDM** print service. Both exceed a
  desktop bed, and 380 mm also exceeds typical MJF and resin build volumes.
- The approved **MEAN WELL GST40A05-P1J, 5 V 6 A** supply with its
  5.5 x 2.1 mm centre-positive plug.

You will also need a chess set whose king base is 32 mm or less, and magnets to
glue into the pieces.

## Board notes for the fab

These are what the generated stack already specifies, listed so an order form can
be filled in without opening the files:

- **Two layers**, 1.6 mm, 320 x 360 mm. Signals on top, a ground pour underneath.
- **0.4 mm traces and 0.4 mm clearance** — four times PCBWay's stated floor,
  because a hand-soldered prototype has no reason to be near a process limit.
- **0.4 mm vias in 0.9 mm pads**, and through-hole pads with a 0.4 mm annular
  ring, which is generous because hand-soldered joints get reworked.
- **Silkscreen on the top only**, carrying the 8 x 8 grid and A1-H8 labels so no
  drawing is needed to know which of 64 identical reed positions you are at.
- **A top paste layer** is emitted for the 64 LEDs, in case anyone wants a
  stencil. The board is meant to be hand-soldered, so it is optional.

## Solder order

Every part is on the top side, so the board never needs turning over. Work from
the flattest parts upward, so each stage still sits flat on the bench.

1. **The 64 SK9822 LEDs.** The only surface-mount parts, and the fiddliest, so do
   them while the board is otherwise bare and flat. Pads are on the sides and
   reachable with a fine tip. Budget an hour and check a few under magnification
   before committing to all 64.
2. **The two DIP sockets' worth of chips — sockets only.** Four 28-pin and one
   14-pin. Leave the chips out; they drop in at the end.
3. **Resistors and the ceramic capacitors.** Two 4.7 k pull-ups and about seventy
   100 nF.
4. **The 64 reed switches.** Bend the leads, keep every body square to its
   square, and keep them lying flat: the plate only clears 4 mm.
5. **The electrolytics**, watching polarity, then the fuse holder.
6. **The twelve buttons and the four-pin display header** on the control strip.
7. **The barrel jack and the rocker switch.**
8. **The 2x20 Pi header**, inserted from underneath and soldered from above so
   the Pi hangs into the case cavity.

## First power-up

Do it before fitting anything expensive.

1. With both chips still out of their sockets and the Pi unplugged, apply power
   and check +5 V and ground at the test points.
2. Check the 3.3 V rail is *absent* — it comes from the Pi's header, so it should
   only appear once the Pi is fitted.
3. Power down, fit the chips and the Pi, power up, and confirm all five I2C
   devices answer at 0x20-0x23 and 0x3C.
4. Probe LED_CLK and LED_DATA at the test points while shifting a frame, before
   worrying about whether the LEDs light.

**Power from the barrel jack only.** The Pi takes 5 V through the header, so also
connecting its micro-USB port puts two supplies in opposition.

## Mechanical assembly

Drop the board onto the case bosses and drive twenty M3 screws into the pilot
holes. Fit the display module into its bezel recess and connect it with a
four-wire jumper. Lay the plate into the rebate — the clipped corner goes to A1 —
and fix it with eight screws into the ledge. Their heads recess below the playing
surface.
