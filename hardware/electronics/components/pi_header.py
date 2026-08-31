"""The Raspberry Pi 40-pin GPIO socket the Pi Zero 2 W plugs into.

This is the only processor on the board. The header is soldered from the top so
the Pi hangs underneath, which keeps every part on one side of the PCB.

Odd pins on the left and even pins on the right, matching how every published
Raspberry Pi pinout is drawn.
"""

from __future__ import annotations

from .connector import pin_header

SUPPLY_3V3_PINS = ("1", "17")
SUPPLY_5V_PINS = ("2", "4")
GND_PINS = ("6", "9", "14", "20", "25", "30", "34", "39")

# Header pin number for each Broadcom GPIO line, as published by Raspberry Pi.
GPIO_TO_PIN = {
    0: "27",
    1: "28",
    2: "3",
    3: "5",
    4: "7",
    5: "29",
    6: "31",
    7: "26",
    8: "24",
    9: "21",
    10: "19",
    11: "23",
    12: "32",
    13: "33",
    14: "8",
    15: "10",
    16: "36",
    17: "11",
    18: "12",
    19: "35",
    20: "38",
    21: "40",
    22: "15",
    23: "16",
    24: "18",
    25: "22",
    26: "37",
    27: "13",
}
PIN_TO_GPIO = {pin: gpio for gpio, pin in GPIO_TO_PIN.items()}

# Alternate functions worth showing on the sheet, so a reader can see why a
# given line was chosen without consulting a table elsewhere.
ALTERNATES = {
    "3": "SDA1",
    "5": "SCL1",
    "8": "TXD",
    "10": "RXD",
    "19": "MOSI",
    "21": "MISO",
    "23": "SCLK",
    "24": "CE0",
    "26": "CE1",
    "27": "ID_SD",
    "28": "ID_SC",
}


def _name(pin: str) -> str:
    if pin in SUPPLY_3V3_PINS:
        return "3V3"
    if pin in SUPPLY_5V_PINS:
        return "5V"
    if pin in GND_PINS:
        return "GND"
    gpio = PIN_TO_GPIO[pin]
    alternate = ALTERNATES.get(pin)
    return f"GPIO{gpio}/{alternate}" if alternate else f"GPIO{gpio}"


PIN_NAMES = {str(pin): _name(str(pin)) for pin in range(1, 41)}
ALL_PINS = tuple(PIN_NAMES)
SIGNAL_PINS = tuple(
    pin
    for pin in ALL_PINS
    if pin not in SUPPLY_3V3_PINS + SUPPLY_5V_PINS + GND_PINS
)

PI_HEADER = pin_header(
    lib="PI_HEADER",
    value="2x20 header",
    description="Raspberry Pi Zero 2 W GPIO socket",
    package="2x20 2.54 mm THT",
    label="Raspberry Pi Zero 2 W",
    left={pin: PIN_NAMES[pin] for pin in ALL_PINS if int(pin) % 2 == 1},
    right={pin: PIN_NAMES[pin] for pin in ALL_PINS if int(pin) % 2 == 0},
)
