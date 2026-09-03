"""Approved physical parts shared by KiCad, CAD, assembly, and purchasing.

Every production component has one stable key and an explicit manufacturer part
number. Domain implementations describe how that real part is represented; they
do not invent package names or substitute anonymous parts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

Implementation = TypeVar("Implementation")


@dataclass(frozen=True)
class ComponentSpec:
    """Approved-part identity and nominal manufacturer L/W/H envelope."""

    key: str
    description: str
    package: str
    manufacturer: str
    mpn: str
    body_mm: tuple[float, float, float] | None = None
    datasheet: str = ""

    def require_body_mm(self) -> tuple[float, float, float]:
        """Return the body envelope, failing clearly when geometry is unspecified."""
        if self.body_mm is None:
            raise ValueError(f"{self.key} has no body dimensions")
        return self.body_mm


# Blender 4.5 embeds Python 3.11, so this shared type cannot use PEP 695 syntax.
class ComponentImplementation(ABC, Generic[Implementation]):  # noqa: UP046
    spec: ComponentSpec

    def __init__(self, spec: ComponentSpec) -> None:
        self.spec = spec

    @abstractmethod
    def build(self) -> Implementation:
        """Build the domain-specific representation of :attr:`spec`."""


def part(
    key: str,
    description: str,
    package: str,
    manufacturer: str,
    mpn: str,
    body_mm: tuple[float, float, float] | None = None,
    datasheet: str = "",
) -> ComponentSpec:
    """Define one exact, purchasable component."""
    if body_mm is not None and any(axis <= 0.0 for axis in body_mm):
        raise ValueError(f"{key}: body dimensions must be positive")
    return ComponentSpec(
        key,
        description,
        package,
        manufacturer,
        mpn,
        body_mm,
        datasheet,
    )


SK9822 = part(
    "SK9822",
    "Clocked 5050 RGB LED",
    "PLCC-6 5050",
    "Opsco Optoelectronics",
    "SK9822-EC20",
    (5.4, 5.0, 1.57),
)
HALL_SENSOR = part(
    "HALL_SENSOR",
    "20 Hz omnipolar active-low Hall-effect sensor",
    "SOT-23-3",
    "Texas Instruments",
    "DRV5032FCDBZR",
    (2.92, 1.30, 1.12),
    "https://www.ti.com/lit/ds/symlink/drv5032.pdf",
)
MCP23017 = part(
    "MCP23017",
    "16-bit I2C GPIO expander",
    "SOIC-28W 1.27 mm",
    "Microchip Technology",
    "MCP23017-E/SO",
    (17.9, 10.3, 2.65),
    "https://ww1.microchip.com/downloads/aemDocuments/documents/APID/"
    "ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf",
)
AHCT125 = part(
    "AHCT125",
    "Quad 3.3 V to 5 V logic buffer",
    "SOIC-14 1.27 mm",
    "Texas Instruments",
    "SN74AHCT125DR",
    (8.7, 6.2, 1.75),
    "https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf",
)
CAP_100N = part(
    "CAP_100N",
    "100 nF 50 V X7R MLCC",
    "0603 (1608 metric)",
    "Yageo",
    "CC0603KRX7R9BB104",
    (1.6, 0.8, 0.8),
)
CAP_10U = part(
    "CAP_10U",
    "10 uF 10 V X5R MLCC",
    "0805 (2012 metric)",
    "Yageo",
    "CC0805KKX5R6BB106",
    (2.0, 1.25, 1.25),
)
CAP_1000U = part(
    "CAP_1000U",
    "1000 uF 10 V low-ESR electrolytic",
    "radial 10 mm",
    "Rubycon",
    "10ZLJ1000M10X16",
    (10.0, 10.0, 16.0),
)
RES_4K7 = part(
    "RES_4K7",
    "4.7 kohm 0.1 W thick-film resistor",
    "0603 (1608 metric)",
    "Yageo",
    "RC0603FR-074K7L",
    (1.6, 0.8, 0.55),
)
BUTTON = part(
    "BUTTON",
    "6 mm tactile switch, 9.5 mm actuator",
    "6x6 mm THT",
    "E-Switch",
    "TL1105SPF100QG",
    (6.0, 6.0, 9.5),
)
PI_ZERO_HEADER = part(
    "PI_ZERO_HEADER",
    "Raspberry Pi Zero 2 W 2x20 socket",
    "2x20 2.54 mm THT",
    "Sullins Connector Solutions",
    "PPPC202LFBN-RC",
)
OLED_HEADER = part(
    "OLED_HEADER",
    "1x4 OLED socket",
    "1x4 2.54 mm THT",
    "Sullins Connector Solutions",
    "PPPC041LFBN-RC",
)
FUSE_2A = part(
    "FUSE_2A",
    "2 A time-delay surface-mount fuse",
    "2410 fuse",
    "Littelfuse",
    "0453002.MR",
    (6.1, 2.7, 2.7),
    "https://www.littelfuse.com/assetdocs/littelfuse-fuse-453-datasheet",
)
BARREL_JACK = part(
    "BARREL_JACK",
    "5.5x2.0 mm centre-positive DC jack, 2.5 A rated",
    "5.5x2.0 mm THT",
    "Same Sky",
    "PJ-102A",
    (14.4, 11.0, 11.0),
    "https://www.sameskydevices.com/product/resource/pj-102a.pdf",
)
TVS_6V8 = part(
    "TVS_6V8",
    "6 V unidirectional TVS diode",
    "SMB (DO-214AA)",
    "Littelfuse",
    "SMBJ6.0A",
    (4.6, 3.6, 2.3),
)
POWER_SWITCH = part(
    "POWER_SWITCH",
    "PCB SPST rocker switch",
    "SPST rocker THT",
    "E-Switch",
    "RA11131100",
)
TEST_POINT = part(
    "TEST_POINT",
    "Low-profile surface-mount test point",
    "SMD test point",
    "Harwin",
    "S1751-46R",
    (2.0, 1.2, 1.0),
)
PI_ZERO_2_W = part(
    "PI_ZERO_2_W",
    "Raspberry Pi Zero 2 W host",
    "65x30 mm module",
    "Raspberry Pi",
    "SC0510",
    (65.0, 30.0, 5.2),
)
OLED_MODULE = part(
    "OLED_MODULE",
    "1.3 inch 128x64 SH1106 four-pin I2C OLED module",
    "36x34 mm module",
    "AZ-Delivery",
    "A 1-6",
    (36.0, 34.0, 3.0),
    "https://www.az-delivery.de/products/1-3zoll-i2c-oled-display",
)
POWER_SUPPLY = part(
    "POWER_SUPPLY",
    "5 V 2 A regulated desktop supply with 5.5x2.1 mm plug",
    "external PSU",
    "MEAN WELL",
    "GST12A05-P1J",
    datasheet="https://www.meanwell.com/Upload/PDF/GST12A/GST12A-SPEC.PDF",
)
MICRO_SD = part(
    "MICRO_SD",
    "32 GB high-endurance microSD card",
    "microSD",
    "SanDisk",
    "SDSQQNR-032G-GN6IA",
)

APPROVED_COMPONENTS = (
    SK9822,
    HALL_SENSOR,
    MCP23017,
    AHCT125,
    CAP_100N,
    CAP_10U,
    CAP_1000U,
    RES_4K7,
    BUTTON,
    PI_ZERO_HEADER,
    OLED_HEADER,
    FUSE_2A,
    BARREL_JACK,
    TVS_6V8,
    POWER_SWITCH,
    TEST_POINT,
    PI_ZERO_2_W,
    OLED_MODULE,
    POWER_SUPPLY,
    MICRO_SD,
)

_component_keys = [spec.key for spec in APPROVED_COMPONENTS]
if len(_component_keys) != len(set(_component_keys)):
    raise ValueError("Approved component keys must be unique")

COMPONENTS = {spec.key: spec for spec in APPROVED_COMPONENTS}
