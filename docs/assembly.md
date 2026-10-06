# Assembly

After assembly, follow the ordered first-article checklist in [bring-up](bring-up.md).

## Before ordering

The SK9822-A LEDs are moisture-sensitivity level 5a: after opening the bag they have a
24 hour floor life before they must be baked, and the TPS259474ARPWR (U74) is level 2.
Plan the reflow accordingly.

Build one DRV5032FC sensor, its 100 nF bypass capacitor, one SK9822-A, and one
TCA9554DWR at the final CAD stack height. Verify reliable operate and release with
both magnet poles, exercise a full eight-sensor bank while updating LEDs,
and record the result in `hardware/pcb/definition/evidence/`.

Run `just --justfile hardware/pcb/justfile release` in the reproducible KiCad container. Fabrication output is
withheld unless tests, ERC, DRC, schematic parity, routing, prototype evidence and
the open-assumptions list (`hardware/pcb/definition/verification.py`) all pass. Also review the fabricator's rendering before payment.

## What to order

`hardware/pcb/generated/bom.md` is generated from the approved exact-MPN catalog and
reviewed netlist; its off-board rows (marked `off-board`) are the parts that do not
solder onto the PCB: the Pi Zero 2 W and its male header, the OLED module, the GST18A05-P1J
5 V 3 A supply, the Switchcraft 722A panel jack, the RA11131100 panel rocker and the
harness wire, housings, contacts and FASTON receptacles.
[`harness.md`](../hardware/pcb/generated/harness.md) lists the harness parts per
harness.

You will also need the two printed parts (an open-tub case and the tile plate with its
control bezel), a chess set with a king base no larger than 32 mm, and magnets for
the pieces.

## Board notes

- Eight copper layers, 1.6 mm finished thickness, 320 x 360 mm.
- 0.31 mm signal traces, 1.5 mm input-power traces, and 0.30 mm clearance.
- Dedicated GND, +5 V, and +3.3 V planes; three internal signal layers.
- SMD assembly on the top side only. Through-hole parts: the TL1105CF100Q buttons on
  top; on the bottom side the Pi socket (J1), the power header (J4) and the two
  560 µF bulk capacitors (C1, C140).

## Suggested assembly order

1. Solder the 0603/0805 passives, Hall sensors, SOIC ICs, SMD fuse/TVS, test
   points, and SK9822 LEDs. Check orientation of every polarized or pin-1 part.
2. Inspect fine-pitch joints and verify that +5 V, +3.3 V, and GND are not
   shorted before fitting through-hole parts.
3. Fit the buttons from the top, then turn the board over and fit the Pi socket,
   the J4 power header and the two bulk capacitors (check capacitor polarity).
   Build the power harness (panel jack and rocker to a VH housing) and the OLED
   harness (four wires soldered to the module, SH housing) per the generated
   [harness table](../hardware/pcb/generated/harness.md); the JST cavity number is
   the header circuit it mates, so check cavity order before plugging in. Fit the
   jack and rocker in the case's rear wall.
4. Clean and inspect the board, then perform current-limited first power-up.

## First power-up

1. Leave the Pi and display unplugged. Measure the supply's open-circuit output (it
   must be below the eFuse's over-voltage lockout, 5.342-5.663 V, and ideally
   at or below the LEDs' 5.3 V recommended maximum), then apply current-limited 5 V at the
   panel jack and verify the protected +5 V rail with the rocker on. The rocker
   enables the eFuse; it does not carry the load. The LED rail (`LED_5V`) stays off
   until firmware sets `LED_EN` (BCM 26), so the LEDs are dark at this point. A 6, 7 or
   12 V adapter is refused safely, but after any over-voltage event unplug and replug;
   do not use a reversed 12 V adapter.
2. Confirm +3.3 V is absent until the Pi is installed; it is supplied by the Pi
   header.
3. Before fitting the OLED module, measure its SDA and SCL to VCC with a meter: the
   board has no I²C pull-ups of its own (only the Pi's 1.8 kΩ), so the module's must
   be 4.7 kΩ or higher, or absent. Power down, install the Pi, then verify TCA9554DWR addresses 0x20-0x27 and the
   display at 0x3C. Follow [polled register setup](host.md#reading-the-board);
   never configure a Hall input as an output. INT pin 13 is deliberately NC on
   every bank; no IRQ pull-up/testpoint is fitted.
4. With the LED rail enabled by firmware (`LED_EN` high, then blank frames for at
   least 10 ms; see [power](power.md#led-rail-switch)), probe buffered LED clock/data (test points TP3/TP4 next to U5 and R9; scope the
   left-turn data link LED_D16 as well) and verify all 64 active-low Hall outputs with a
   magnet before mechanical assembly. Measure Hall release edges/noise and
   SDA/SCL rise times at the furthest banks during LED updates (the bus is specified
   for the Pi's default 100 kHz only; do not raise the I²C rate). Record real
   D-PROTOTYPE evidence, including final CAD spacing; generated checks alone
   do not qualify the weak pull-ups or bus timing.

Power the finished board from the panel jack only. **Never power the Pi from its own
micro-USB port while it is fitted to the board:** its 5 V is tied to the board's `+5V`
rail through the header, so USB power would feed all 64 LEDs with no fuse in the path.
Use USB power only with the Pi removed from the board.

Protection: the harness's circuit 4 is the eFuse enable (`RUN`), not the switched rail;
follow the generated harness table. See [power](power.md) for the protection design and
what is still unverified. At first power-up also measure the board's over-voltage trip
and restart points with a lab supply, check the rocker switches reliably at its roughly
5 mA wetting load, and, if the Pi reports under-voltage at a low supply, check
`vcgencmd get_throttled` (the Pi's 4.63 V level is not met at the worst corner).
