"""KiCad footprints and approved PCB bindings for the LED rail switch (S6, H5).

Q1 is the Vishay Si4403DDY P-MOSFET (SO-8) between +5V and LED_5V; Q2 the onsemi
BSS138LT1G N-MOSFET (SOT-23) that turns LED_EN into the active-low LED_EN_N; U75 (S6b)
is the SN74LVC1G97 gate that holds the 74AHCT125 outputs off until LED_5V is up. Wiring
is in `assemblies/led_switch.py`. Pin identities: `shared/electronics/mosfet.py`.
"""

import pcbnew

from pcb.definition.parts.land_patterns import (
    add_polarity_marker,
    courtyard_for,
    footprint,
    pad,
    soic,
)
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import LED_ENABLE_GATE, LED_SWITCH, LED_SWITCH_DRIVER
from shared.electronics.mosfet import LogicGateComponent as LogicGate
from shared.electronics.mosfet import LogicGatePin, PowerMosfetPin, SmallMosfetPin
from shared.electronics.mosfet import PowerMosfetComponent as PowerMosfet
from shared.electronics.mosfet import SmallMosfetComponent as SmallMosfet

# Vishay AN826 "Recommended minimum pads for SO-8" (doc 72606 p22, as reproduced in
# the Si4403DDY sheet; current doc 72286 p33, same land): 0.559 x 1.194 mm pads at 1.270 pitch, rows 3.861
# apart inside (6.248 outside), so pad centres 5.055 apart.
LED_SWITCH_FOOTPRINT = soic(
    "SO-8 1.27 mm",
    "Si4403DDY P-channel MOSFET",
    8,
    3.861 + 1.194,
    (6.2, 5.0),
    tuple(PowerMosfetPin),
    pad_size_mm=(1.194, 0.559),
)
