# Hardware design

D-PROTOTYPE is a fixed-function sensor-and-light PCB connected directly to a Raspberry
Pi Zero 2 W. There is no microcontroller and no separate schematic source tree.

## Sources of truth

- [`hardware/shared/wiring.py`](../hardware/shared/wiring.py) owns net names,
  GPIO assignments, expander mapping, and LED chain order.
- [`hardware/shared/components.py`](../hardware/shared/components.py) owns stable
  component identities and physical package metadata.
- [`hardware/shared/dimensions.py`](../hardware/shared/dimensions.py) owns the
  board envelope and feature positions shared with CAD.
- [`hardware/pcb/board/netlist.json`](../hardware/pcb/board/netlist.json) is the
  reviewed component and connectivity contract.
- [`hardware/pcb/generated/bom.md`](../hardware/pcb/generated/bom.md) is the
  generated assembly manifest.

The PCB implementation supplies footprints, placement, routing, and fabrication
output for those shared definitions. This avoids maintaining a drawing that can
drift from the board actually sent to fabrication.

## Architecture

Eight TI TCA9554DWR expanders read all 64 DRV5032FC active-low omnipolar Hall
sensors. Each owns a compact 2-rank × 4-file bank and all eight P0–P7 inputs. Sixty-four SK9822 LEDs form a serpentine SPI chain beginning at
A1. Twelve panel buttons connect to dedicated Pi GPIO lines, and an SH1106 OLED
uses the shared I²C bus.

`hardware/shared/hall_banks.py` defines bank membership, input order, address
straps, and labels once. Shared dimensions derive placement from bank geometry
and package/LED clearance; PCB generation checks the reviewed JSON netlist
against that mapping. CAD depicts the same eight package obstructions.

Banks use 0x20–0x27; the OLED remains 0x3C. Acquisition is polled, with each INT
and GPIO4 explicitly no-connect. See [host acquisition](host.md#reading-the-board)
for register setup, non-atomic scans, pull-up assumptions, and required testing.
The SOIC-16W land pattern follows TI DW0016A (SCPS233E pp. 39–40): 1.27 mm pitch,
9.3 mm pad-row spacing, 2.0 × 0.6 mm lands. This is not a scaled old package.

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

PCB tests verify package coverage, pad numbering, placement, fabrication rules,
and connectivity, including native-board/schematic parity. `just pcb-release`
also requires real prototype evidence before fabrication export; a review pass
is not physical approval.
