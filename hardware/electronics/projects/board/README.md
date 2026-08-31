# Single board

`generate.py` owns the whole revision-B schematic. There is one sheet because
there is one PCB: 5 V input, the Raspberry Pi Zero 2 W socket, four I2C
expanders reading 64 reed switches, the SK9822 LED chain, and the control panel.

Published output is `board.svg` and `board.png` in
`hardware/electronics/generated`, with quantities in `bom.md`.

## Design rules

The board is meant to be reviewed by someone who is not an electrical engineer
and assembled by hand. That produces three hard rules:

- **Two IC part numbers only**, MCP23017 and SN74AHCT125N, both in DIP sockets
  so no chip is ever soldered.
- **Through-hole everywhere except the LEDs.** Leaded resistors, ceramic discs,
  radial electrolytics, axial reeds.
- **Every part on the top side.** One soldering surface, no flipping. The Pi
  header is fitted from below and soldered from above so the Pi hangs into the
  case cavity.

## No microcontroller

The Pi does everything directly, which is only possible because of two part
choices:

- Reed switches get **one expander pin each** instead of being scanned as a
  matrix. That deletes 64 isolation diodes and makes ghosting impossible.
- The LEDs are **SK9822**, which carry their own clock line. The chain is an
  ordinary SPI shift register with no timing requirement, so a stalled Linux
  scheduler latches late instead of corrupting a frame. A WS2812B would have
  needed PWM with DMA, root privileges and the audio peripheral.

The result is one Rust binary and no firmware.

## Bus and line assignment

| Function | Where |
|---|---|
| Reed inputs | MCP23017 at 0x20-0x23, one per 4x4 quadrant |
| Display | SSD1306 at 0x3C on the same I2C bus |
| LED data, clock | GPIO10 and GPIO11 through the buffer |
| Sensor interrupt | GPIO4, wired-OR from four INTA pins |
| Panel buttons | GPIO5, 6, 12, 13, 16, 17, 19, 20, 21, 22, 23, 24 |

`core/names.py` owns every one of those assignments, so the schematic and the
host software have a single place to agree.

## Power

A 5 V 5 A brick feeds a barrel jack through a fuse, a clamp and a rocker. The
3.3 V rail comes off the Pi's header, which the expanders and display are small
enough to allow. 64 LEDs at unrestricted full white would draw about 3.84 A, so
the host caps brightness using the SK9822 per-LED brightness field.

Do not power the Pi's micro-USB while the jack is connected.

## Before ordering

The reed switches lie flat under a vertically-oriented piece magnet, so they
couple through the field's horizontal fringe rather than head-on. Build the
single-square test in `../../prototype/` first: one reed, one LED, one expander.
A sensitivity problem found after ordering five 320 x 360 mm boards is expensive.

Run `./tools/electronics` from the repository root.
