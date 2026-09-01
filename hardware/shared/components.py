"""Approved physical parts shared by KiCad, CAD, assembly, and purchasing.

Every production component has one stable key and an explicit manufacturer part
number. Domain implementations describe how that real part is represented; they
do not invent package names or substitute anonymous parts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar


@dataclass(frozen=True)
class ComponentSpec:
    key: str
    description: str
    package: str
    manufacturer: str
    mpn: str
    body_mm: tuple[float, float, float] | None = None
    datasheet: str = ""


Implementation = TypeVar("Implementation")


class ComponentImplementation(ABC, Generic[Implementation]):
    spec: ComponentSpec

    def __init__(self, spec: ComponentSpec) -> None:
        self.spec = spec

    @abstractmethod
    def build(self) -> Implementation:
        """Build the domain-specific representation of :attr:`spec`."""


def part(key, description, package, manufacturer, mpn, body=None, datasheet=""):
    return ComponentSpec(key, description, package, manufacturer, mpn, body, datasheet)


SK9822 = part("SK9822", "Clocked 5050 RGB LED", "PLCC-6 5050", "Opsco Optoelectronics", "SK9822-EC20", (5.4, 5.0, 1.57))
REED_SWITCH = part("REED_SWITCH", "Normally-open axial reed switch", "axial 14 mm", "Standex-Meder Electronics", "KSK-1A66-1015", (14.0, 2.2, 2.2))
MCP23017 = part("MCP23017", "16-bit I2C GPIO expander", "PDIP-28", "Microchip Technology", "MCP23017-E/SP", (34.7, 7.6, 4.6), "https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf")
AHCT125 = part("AHCT125", "Quad 3.3 V to 5 V logic buffer", "DIP-14", "Texas Instruments", "SN74AHCT125N", (19.3, 6.35, 4.57), "https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf")
CAP_100N = part("CAP_100N", "100 nF radial ceramic capacitor", "disc 2.54 mm", "KEMET", "C315C104M5U5TA")
CAP_10U = part("CAP_10U", "10 uF 16 V radial electrolytic", "radial 5 mm", "Nichicon", "UVR1C100MDD")
CAP_1000U = part("CAP_1000U", "1000 uF 10 V low-ESR electrolytic", "radial 10 mm", "Panasonic", "EEU-FR1A102")
RES_4K7 = part("RES_4K7", "4.7 kohm 0.25 W axial resistor", "axial 1/4 W", "Yageo", "MFR-25FBF52-4K7")
BUTTON = part("BUTTON", "6 mm tactile switch, 9.5 mm actuator", "6x6 mm THT", "Omron", "B3F-4050")
PI_ZERO_HEADER = part("PI_ZERO_HEADER", "Raspberry Pi Zero 2 W 2x20 socket", "2x20 2.54 mm THT", "Samtec", "SSW-120-02-G-D")
OLED_HEADER = part("OLED_HEADER", "1x4 OLED socket", "1x4 2.54 mm THT", "Samtec", "SSW-104-02-G-S")
DIP28_SOCKET = part("DIP28_SOCKET", "28-pin turned-pin DIP socket", "DIP-28", "Mill-Max", "110-44-628-41-001000")
DIP14_SOCKET = part("DIP14_SOCKET", "14-pin turned-pin DIP socket", "DIP-14", "Mill-Max", "110-44-314-41-001000")
FUSE_HOLDER = part("FUSE_HOLDER", "5x20 mm PCB fuse holder", "5x20 mm holder THT", "Keystone Electronics", "3557")
FUSE_5A = part("FUSE_5A", "5 A time-delay 5x20 mm fuse", "5x20 mm fuse", "Littelfuse", "0218005.MXP")
BARREL_JACK = part("BARREL_JACK", "5.5x2.0 mm centre-positive DC jack", "5.5x2.0 mm THT", "Same Sky", "PJ-102A", datasheet="https://www.sameskydevices.com/product/resource/pj-102a.pdf")
TVS_6V8 = part("TVS_6V8", "6.8 V unidirectional TVS diode", "axial DO-15", "Littelfuse", "P6KE6.8A")
POWER_SWITCH = part("POWER_SWITCH", "PCB SPST rocker switch", "SPST rocker THT", "E-Switch", "RA11131100")
TEST_POINT = part("TEST_POINT", "1.6 mm turret test point", "turret 1.6 mm THT", "Keystone Electronics", "1502-2")
PI_ZERO_2_W = part("PI_ZERO_2_W", "Raspberry Pi Zero 2 W host", "65x30 mm module", "Raspberry Pi", "SC0510", (65.0, 30.0, 5.2))
OLED_MODULE = part("OLED_MODULE", "1.3 inch 128x64 I2C OLED module", "35.5x33.5 mm module", "Waveshare", "1.3inch OLED (A) 10444", (35.5, 33.5, 4.0))
POWER_SUPPLY = part("POWER_SUPPLY", "5 V 6 A regulated desktop supply", "external PSU", "MEAN WELL", "GST40A05-P1J")
MICRO_SD = part("MICRO_SD", "32 GB high-endurance microSD card", "microSD", "SanDisk", "SDSQQNR-032G-GN6IA")

COMPONENTS = {
    spec.key: spec
    for spec in (
        SK9822, REED_SWITCH, MCP23017, AHCT125, CAP_100N, CAP_10U,
        CAP_1000U, RES_4K7, BUTTON, PI_ZERO_HEADER, OLED_HEADER,
        DIP28_SOCKET, DIP14_SOCKET, FUSE_HOLDER, FUSE_5A, BARREL_JACK,
        TVS_6V8, POWER_SWITCH, TEST_POINT, PI_ZERO_2_W, OLED_MODULE,
        POWER_SUPPLY, MICRO_SD,
    )
}
