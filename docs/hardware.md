# Hardware design

D-PROTOTYPE is a fixed-function sensor-and-light PCB connected directly to a Raspberry
Pi Zero 2 W, which hangs under the board and plugs into a socket (J1) on the board's
bottom side. There is no microcontroller and no separate schematic source tree.

## Sources of truth

- [`hardware/shared/wiring.py`](../hardware/shared/wiring.py) owns net names,
  GPIO assignments, expander mapping, and LED chain order.
- [`hardware/shared/components/`](../hardware/shared/components/) contains one
  approved-product file per part, with its identity and physical package metadata.
- [`hardware/shared/dimensions/board.py`](../hardware/shared/dimensions/board.py) owns
  the playing grid and PCB envelope; the neighboring case, panel, and tile-plate
  modules own their physical measurements.
- [`hardware/pcb/board/board.py`](../hardware/pcb/board/board.py) composes
  the component instances and their declared connectivity.
- [`hardware/shared/electronics/harness.py`](../hardware/shared/electronics/harness.py)
  defines the off-board wiring harnesses (power entry, OLED) cavity by cavity.
- [`hardware/pcb/generated/bom.csv`](../hardware/pcb/generated/bom.csv) lists the
  PCB components. Off-board assembly output still needs migration.

The PCB implementation supplies footprints, placement, routing, and fabrication
output for those shared definitions. This avoids maintaining a drawing that can
drift from the board actually sent to fabrication.

## Architecture

Eight TI TCA9554DWR expanders read all 64 DRV5032FC active-low omnipolar Hall
sensors. Each owns a compact 2-rank × 4-file bank and all eight P0–P7 inputs. Sixty-four Opsco SK9822-A LEDs (GRB colour order, budgeted at 18 mA per channel) form a serpentine
SPI chain beginning at A1, powered from a switchable `LED_5V` rail that is off at boot (see
[power](power.md#led-rail-switch)); the Pi's 3.3 V SPI clock and data reach the 5 V
chain through a 74AHCT125 buffer (U5, held off by a SN74LVC1G97 gate, U75, until the LED rail is up) and a 56 Ω series resistor (R9) that damps the
first link. Later LED links run over a plane reference, and the three left rank-turn
data links carry their own 56 Ω series resistors (R10-R12). Twelve E-Switch TL1105CF100Q panel buttons
connect to dedicated Pi GPIO lines, and an SSD1309 OLED module on the shared I²C
bus is wired to a JST SH header (J2) and sits in the tile plate's bezel.

`hardware/shared/hall_banks.py` defines bank membership, input order, address
straps, and labels once. Shared dimensions derive placement from bank geometry
and package/LED clearance; PCB generation composes and validates the typed electrical graph
against that mapping. CAD depicts the same eight package obstructions.

Banks use 0x20–0x27; the OLED remains 0x3C. Acquisition is polled, with each INT
and GPIO4 explicitly no-connect. See [host acquisition](host.md#reading-the-board)
for register setup, non-atomic scans, pull-up assumptions, and required testing.
The SOIC-16W land pattern follows TI DW0016A (SCPS233E pp. 39–40): 1.27 mm pitch,
9.3 mm pad-row spacing, 2.0 × 0.6 mm lands. This is not a scaled old package.

## Power entry and bottom side

The 5 V supply enters through a panel jack and a panel rocker in the case's rear
wall, wired to a JST VH header (J4) on the board; see [power](power.md) for the eFuse protection (the rocker
switches the eFuse's enable signal, not the load). Only
through-hole parts sit on the bottom side: J1 (the Pi socket), J4 and the two bulk
capacitors. Everything else is top side.

## Buses and LED lines (S5)

- **I²C:** the PCB has no pull-ups (R1/R2 removed). The Pi supplies 1.8 kΩ;
  the approved MC242GW module adds 4.7 kΩ on each line to its 3.3 V logic rail
  ([supplier schematic](https://www.lcdwiki.com/res/MC242GX/2.42inch_IIC_Module_MC242GX_Schematic.pdf)).
  Their nominal parallel resistance is 1.30 kΩ: the existing capacitance estimates
  of 243 pF SDA / 230 pF SCL imply about 268 / 254 ns rise time using 0.8473RC,
  with about 2.23 mA sink current at 0.4 V. These are estimates, not measured bus
  timing. Firmware retains the Pi's default **100 kHz**; this change does not qualify
  400 kHz. Verify the supplied module variant and measure the populated bus.
- **LED lines:** the LED rail is an inner plane, so the outer-layer links are
  referenced to it. The first data link (through R9) and the clock stay within the
  SK9822's input range at 4.5 V and 5.25 V in simulation (lossless-line model, assumed
  25-100 Ω driver, 1-3 ns edges). Rank-turn links are plane-referenced. The three left
  rank-turn data links (LED_D16/D32/D48, on an inner layer) were out of range without
  a terminator and pass with R10-R12 (56 Ω, 3 mm after each LED's data output). Edges
  settle in at most about 6 ns, well inside the SK9822-A's 30 MHz serial limit.
  The SK9822-A's driver strength is not in its datasheet, so a bench scope of LED_D16 at
  the SPI clock remains. Test points TP3/TP4 sit next to U5/R9. The datasheet's
  optional 500 Ω series resistors are not fitted. R9 is kept as margin; R17/R18 (10 kΩ) hold LED_DATA_5V and LED_CLK_5V low while the buffer is off. The SPI clock
  is limited to 10 MHz, which leaves a worst-case data setup margin of about 33 ns
  against the SK9822-A (about 1.5 ns would remain at 30 MHz).

The single PCB retains its validated eight-layer, 1.6 mm stackup. No compatible
layer reduction or physical operation has been established. Hall routes are
confined to their bank rectangles; native-board tests separately bound copper
length and footprint-centre distance rather than conflating them.

## Validation

Run:

```sh
just --justfile hardware/shared/justfile check
just --justfile hardware/pcb/justfile review
```

PCB checks cover component declarations, pin maps, package geometry, documentation
URLs and native PCB checks. Generation requires zero routed-copper DRC violations,
unconnected pads and schematic parity mismatches. Board pytest/SPICE scenarios
cover Hall sensing, bypass charging and button presses, chords, bounce and release.
Power-path, ampacity, bus timing and firmware pin parity checks still need migration;
older calculated figures in these documents are retained assumptions, not current
validation. See the [PCB README](../hardware/pcb/README.md).

`just pcb-release` currently refuses manufacturing approval. Review the
[engineering assumptions](pcb-assumptions.md) and record real prototype evidence
before treating the generated files as a physically validated design.
