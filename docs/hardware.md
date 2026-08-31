# Hardware

## Purpose

Describe the physical board: what senses the pieces, what lights the squares,
and what decides.

## One board, no microcontroller

The revision-B schematic is generated from
[`hardware/electronics/projects/board/generate.py`](../hardware/electronics/projects/board/generate.py).
There is one sheet because there is one PCB: 320 x 360 mm, carrying 64 reed
switches, 64 SK9822 LEDs, the control panel and a socket for the host.

A **Raspberry Pi Zero 2 W** is the only processor. It reads the sensors over
I2C, shifts the LED frame out over SPI, and reads the panel buttons on plain
GPIO lines. Nothing on the board runs code, so the product is one Rust binary
and there is no firmware to write, no cross-compilation target and no flashing
step.

That is only possible because of two component choices:

- **Every reed switch gets its own input pin** across four MCP23017 expanders —
  64 pins across four chips, exactly. No matrix scanning, so no ghosting and no
  scan timing. The 64 isolation diodes a scanned matrix needs are gone.
- **The LEDs are SK9822**, which carry a separate clock line. The chain is an
  ordinary SPI shift register with no timing requirement at all: a host that
  stalls between bytes latches late rather than corrupting the frame. A WS2812B
  resets after about 50 µs of idle, which is exactly why driving one from Linux
  needs PWM with DMA, root privileges and the audio peripheral.

## Bus and line assignment

`hardware/electronics/core/names.py` owns every assignment below. It is the
single place the schematic and the host software agree, and
`crates/board-model` is checked against it.

| Function | Where |
|---|---|
| Reed inputs | MCP23017 at 0x20-0x23, one per 4x4 quadrant |
| Display | SSD1306 OLED at 0x3C, same I2C bus |
| LED data, clock | GPIO10 and GPIO11, through the level buffer |
| Sensor interrupt | GPIO4, wired-OR from four INTA pins |
| Panel buttons | GPIO5, 6, 12, 13, 16, 17, 19, 20, 21, 22, 23, 24 |

Expanders are addressed by quadrant: the index is `(rank / 4) * 2 +
(file / 4)`, strapped onto the device's own address pins, which is why the four
addresses run consecutively. Within a quadrant, port A takes the lower two ranks.
Quadrants exist to keep reed traces short on a board this size — no run exceeds
about 85 mm.

The LED chain snakes by rank from a1, so the gap between consecutive LEDs is one
square pitch everywhere.

## The one part that cannot be removed

An **SN74AHCT125N** buffer translates the SPI clock and data from 3.3 V to 5 V.
SK9822 needs roughly 0.7 × VDD for a valid logic high, so about 3.5 V at a 5 V
supply, and the Pi drives 3.3 V. Every alternative is a worse trick: dropping the
LED rail through a Schottky means dissipating watts in a diode, and running out
of spec means it works until it does not.

Two of its four channels carry the chain. The spares are held disabled with their
inputs tied to ground rather than left floating.

## Built to be assembled by hand

The board has **two IC part numbers** and about eighteen things to buy. Both ICs
are through-hole in sockets, so no chip ever sees a soldering iron and a fried
one is a thirty-second swap. Every passive is leaded, all twelve panel buttons
are the same tactile switch, and every part mounts on the top side so there is
one soldering surface. The 64 LEDs are the only surface-mount parts.

`hardware/electronics/tests` enforces those constraints, so a change that
quietly introduces a surface-mount part or lengthens the purchase list fails the
build.

## Open question before ordering

Reed sensitivity is unproven. The reeds lie flat under a vertically oriented
piece magnet, so they couple through the field's horizontal fringe rather than
head-on. This is inherited from revision A rather than new. Build the
single-square test in `hardware/electronics/prototype/` — one reed, one LED, one
expander — before ordering a full board.

There is also no PCB layout in this repository. The electronics tooling draws
schematics and counts a bill of materials; producing Gerbers is a separate step
in a tool that does not exist here yet.
