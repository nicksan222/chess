"""KiCad footprint and approved PCB bindings for the Yageo 0603 resistors.

Role: the eFuse limit/divider/wetting resistors R3-R8 (`assemblies/power.py`) and
the LED data terminators R9-R12. The land follows the Yageo mounting table below.
"""

from pcb.definition.parts.land_patterns import two_terminal_smd
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import (
    RES_1K,
    RES_1K65,
    RES_10K,
    RES_56,
    RES_100K,
    RES_169K_PRECISION,
    RES_261K,
    RES_604K_PRECISION,
    ComponentSpec,
)
from shared.electronics.passives import ResistorComponent as Resistor
from shared.electronics.passives import ResistorPin

# Yageo chip resistor mounting (2018-02-13 V.10) p4 Table 1, 0603: C 0.9 land
# length, D 0.8 width, B 0.8 gap.
RESISTOR_FOOTPRINT = two_terminal_smd(
    "0603 (1608 metric)",
    "0603 chip resistor",
    0.8 + 0.9,
    (0.9, 0.8),
    (1.6, 0.8),
    tuple(ResistorPin),
)

RES_1K_PART = PcbPart(
    RES_1K,
    Resistor,
    RESISTOR_FOOTPRINT,
    "R",
    "4.7k",
    RES_4K7.description,
)
