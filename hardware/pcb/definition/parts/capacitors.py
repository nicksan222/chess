"""KiCad footprint and approved PCB binding for capacitors."""

from pcb.definition.parts.land_patterns import two_pad_axial, two_terminal_smd
from pcb.definition.parts.part import PcbPart
from shared.components import CAP_10U, CAP_100N, CAP_1000U
from shared.electronics.passives import CapacitorComponent as Capacitor
from shared.electronics.passives import CapacitorPin

CAPACITOR_0603_FOOTPRINT = two_terminal_smd(
    "0603 (1608 metric)",
    "100 nF X7R MLCC",
    1.5,
    (0.9, 0.95),
    (1.6, 0.8),
    tuple(CapacitorPin),
)

CAPACITOR_0805_FOOTPRINT = two_terminal_smd(
    "0805 (2012 metric)",
    "10 uF X5R MLCC",
    1.9,
    (1.0, 1.4),
    (2.0, 1.25),
    tuple(CapacitorPin),
)

CAPACITOR_ELECTROLYTIC_10MM = two_pad_axial(
    "radial 10 mm",
    "1000 uF radial electrolytic",
    pitch=5.0,
    lead_diameter=0.8,
    body=(10.5, 10.5),
    pin_numbers=tuple(CapacitorPin),
)

CAP_100N_PART = PcbPart(
    CAP_100N,
    Capacitor,
    CAPACITOR_0603_FOOTPRINT,
    "C",
    "100nF",
    CAP_100N.description,
)
CAP_10U_PART = PcbPart(
    CAP_10U,
    Capacitor,
    CAPACITOR_0805_FOOTPRINT,
    "C",
    "10uF 10V",
    CAP_10U.description,
)
CAP_1000U_PART = PcbPart(
    CAP_1000U,
    Capacitor,
    CAPACITOR_ELECTROLYTIC_10MM,
    "C",
    "1000uF 10V",
    CAP_1000U.description,
)
