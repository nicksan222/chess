"""KiCad footprints and approved PCB bindings for the capacitors.

Role: 0603 (100 nF decoupling, 10 nF eFuse timing/filter, 1 uF eFuse input), 0805 (10 uF
rail) ceramics and the 8 mm radial electrolytic used for the two bulk capacitors. No
Yageo land drawing is on file for the ceramics, so they use Murata's reflow lands for the
same EIA size (an ASSUMPTION in `definition/verification.py`). Pin identities:
`shared/electronics/passives.py`.
"""

from pcb.definition.parts.land_patterns import (
    add_polarity_marker,
    two_pad_axial,
    two_terminal_smd,
)
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import CAP_1N, CAP_1U, CAP_10N, CAP_10U, CAP_100N, CAP_560U
from shared.electronics.passives import CapacitorComponent as Capacitor
from shared.electronics.passives import CapacitorPin

# Murata JEMCGC-2701X p25 Table 2 (reflow), 1.6x0.8 within ±0.10: gap a 0.6-0.8,
# land b 0.6-0.7, width c 0.6-0.8; mid-range values. No Yageo land is on file.
CAPACITOR_0603_FOOTPRINT = two_terminal_smd(
    "0603 (1608 metric)",
    "100 nF X7R MLCC",
    0.7 + 0.65,
    (0.65, 0.7),
    (1.6, 0.8),
    tuple(CapacitorPin),
)

# Murata JEMCGC-2701X p25 Table 2 (reflow), 2.0x1.25 ±0.20: gap a 1.0-1.4, land
# b 0.6-0.8, width c 1.2-1.4; mid-range values.
CAPACITOR_0805_FOOTPRINT = two_terminal_smd(
    "0805 (2012 metric)",
    "10 uF X5R MLCC",
    1.2 + 0.7,
    (0.7, 1.3),
    (2.0, 1.25),
    tuple(CapacitorPin),
)

# Through-hole radial part; the polarity dot marks the positive lead.
CAPACITOR_ELECTROLYTIC_8MM = two_pad_axial(
    "radial 8 mm",
    "560 uF radial electrolytic",
    # Rubycon ZLJ p2: φD 8 => lead φd 0.6, F 3.5; body φD + 0.5 max.
    pitch=3.5,
    lead_diameter=0.6,
    body=(8.5, 8.5),
    pin_numbers=tuple(CapacitorPin),
)
add_polarity_marker(CAPACITOR_ELECTROLYTIC_8MM, "1")

CAP_100N_PART = PcbPart(
    CAP_100N,
    Capacitor,
    CAPACITOR_0603_FOOTPRINT,
    "C",
    "100nF",
    CAP_100N.description,
    DrawingView.MOUNTING_SIDE,
)
CAP_10U_PART = PcbPart(
    CAP_10U,
    Capacitor,
    CAPACITOR_0805_FOOTPRINT,
    "C",
    "10uF 10V",
    CAP_10U.description,
    DrawingView.MOUNTING_SIDE,
)
CAP_560U_PART = PcbPart(
    CAP_560U,
    Capacitor,
    CAPACITOR_ELECTROLYTIC_8MM,
    "C",
    "1000uF 10V",
    CAP_1000U.description,
)
