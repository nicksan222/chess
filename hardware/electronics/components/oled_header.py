"""Four-pin header for the SSD1306 OLED module.

The display is a plug-in module joined by a short jumper cable, so it puts no
circuitry on the PCB and the case can hold it at whatever height reads best.
Pin order matches the common breakout: ground, supply, clock, data.
"""

from __future__ import annotations

from .connector import pin_header

GND_PIN = "1"
SUPPLY_PIN = "2"
SCL_PIN = "3"
SDA_PIN = "4"

PIN_NAMES = {
    GND_PIN: "GND",
    SUPPLY_PIN: "VCC",
    SCL_PIN: "SCL",
    SDA_PIN: "SDA",
}

OLED_HEADER = pin_header(
    lib="OLED_HEADER",
    value="1x4 header",
    description="SSD1306 OLED module connector",
    package="1x4 2.54 mm THT",
    label="SSD1306 OLED",
    left=PIN_NAMES,
    pinspacing=1.6,
)
