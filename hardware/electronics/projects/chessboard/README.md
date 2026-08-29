# Complete chessboard

`generate.py` owns the full revision-A schematic: battery power, Pico 2 W,
level shifter, 8×8 reed matrix, and serpentine LED chain. It places sixty-four
copies of the shared square cells from `blocks/` plus the controller and
power subsystems.

Published output is `chessboard.svg` and `chessboard.png` in
`hardware/electronics/generated`, plus this project's section of
[`bom.md`](../../generated/bom.md).

## Controller assignment

| Function | Pico GPIO |
|---|---|
| WS2812 data | GP0 |
| Matrix rows 0–7 | GP1–GP8 |
| Matrix columns 0–7 | GP9–GP16 |
| Battery ADC | GP26 / ADC0 |

Every matrix column has a 10 kΩ pull-up to 3.3 V. Each normally-open reed switch
has a 1N4148W isolation diode. Firmware drives exactly one row low, leaves all
other rows high-impedance, and reads the columns.

The LED chain snakes by rank from A1. A 74AHCT1G125 translates Pico data to 5 V
and a 330 Ω resistor provides source termination. Each WS2812B has local 100 nF
decoupling.

## Power

Six removable AA NiMH cells feed a 5 A fuse, latching switch, and Pololu
D36V50F5 5 V/5 A regulator. Charging is intentionally external. The LEDs can
draw approximately 3.84 A at unrestricted full white, so firmware should cap
normal aggregate brightness and the harness must inject 5 V and ground at every
physical LED row.

A 100 kΩ/39 kΩ divider feeds GP26/ADC0 through a 10 kΩ fault-current limiting
resistor. An 8.7 V battery pack produces approximately 2.44 V at the ADC.

## Prototype gates

Before fabrication:

1. Confirm reed sensitivity through the real tile and magnet stack.
2. Load-test the regulator, fuse, switch, connectors, and conductors.
3. Measure far-end LED voltage and adjust power injection.
4. Verify LED timing and matrix polarity with firmware.
5. Review every assigned package and the physical harness layout.

Run `make electronics` from the repository root.
