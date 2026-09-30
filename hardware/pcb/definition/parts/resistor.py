"""KiCad footprint and approved PCB binding for resistor."""

from pcb.definition.parts.land_patterns import two_terminal_smd
from pcb.definition.parts.part import PcbPart
from shared.components import RES_4K7
from shared.electronics.passives import ResistorComponent as Resistor
from shared.electronics.passives import ResistorPin

RESISTOR_FOOTPRINT = two_terminal_smd(
    "0603 (1608 metric)",
    "4.7 kΩ thick-film resistor",
    1.5,
    (0.9, 0.95),
    (1.6, 0.8),
    tuple(ResistorPin),
)

RES_4K7_PART = PcbPart(
    RES_4K7,
    Resistor,
    RESISTOR_FOOTPRINT,
    "R",
    "4.7k",
    RES_4K7.description,
)
