# Hardware

## Purpose

Summarize validated physical-system decisions.

## Prototype electrical design

The complete revision-A prototype schematic is generated from
[`hardware/electronics/projects/chessboard/generate.py`](../hardware/electronics/projects/chessboard/generate.py).
The single-square cell is generated from
[`hardware/electronics/projects/square/generate.py`](../hardware/electronics/projects/square/generate.py).
Shared cells and parts live beside those projects. It uses a Raspberry Pi Pico
2 W, an 8 by 8 normally-open reed matrix with one 1N4148W isolation diode per
square, and a serpentine chain of 64 WS2812B RGB LEDs. A 74AHCT1G125 provides a
valid 5 V LED data signal from the Pico's 3.3 V GPIO.

The sensor rows use GP1-GP8 and columns use GP9-GP16. Each column has an
external 10 kΩ pull-up. The generated design preserves an A1-H8 mapping for
both sensors and LEDs.

## TODO

Physically validate reed sensitivity, regulator and wiring thermal performance,
voltage drop, LED timing, matrix scanning, exact footprints, PCB/harness layout,
and mechanical integration before treating revision A as production hardware.
