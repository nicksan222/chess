# Hardware design

Revision B is a passive sensor-and-light PCB connected directly to a Raspberry
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

Four MCP23017 expanders read 64 active-low omnipolar Hall sensors. Each expander owns
a 4×4 quadrant. Sixty-four SK9822 LEDs form a serpentine SPI chain beginning at
A1. Twelve panel buttons connect to dedicated Pi GPIO lines, and an SSD1306 OLED
uses the shared I²C bus.

The host mapping test in `hardware/shared/tests/test_host_agreement.py` verifies
that Rust interprets expander bytes and LED indices using the same formulas as
the hardware contract.

## Validation

Run:

```sh
just --justfile hardware/shared/justfile check
just --justfile hardware/pcb/justfile release
```

PCB tests verify package coverage, pad numbering, placement, fabrication rules,
and connectivity. Fabrication archives remain withheld while declared
connections are unrouted.
