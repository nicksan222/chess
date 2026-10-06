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
add_polarity_marker(LED_SWITCH_FOOTPRINT, "1")

# onsemi BSS138LT1/D Rev 15 (Sept 2026), case 318 Issue AU (98ASB42226B) p7
# recommended mounting footprint: three 0.56 wide x 0.95 long pads, 0.95 pitch,
# 2.90 overall, so pad centres +/-0.975 (S6b, manufacturing review; replaces the
# superseded 318-08 0.80 x 0.90 land). Top view: pins 1 (gate) and 2 (source) on
# one side, 3 (drain) opposite.
LED_SWITCH_DRIVER_PADS = (
    pad(SmallMosfetPin.GATE, -0.95, -0.975, 0.56, 0.95, pcbnew.PAD_SHAPE_RECT),
    pad(SmallMosfetPin.SOURCE, 0.95, -0.975, 0.56, 0.95, pcbnew.PAD_SHAPE_OVAL),
    pad(SmallMosfetPin.DRAIN, 0.0, 0.975, 0.56, 0.95, pcbnew.PAD_SHAPE_OVAL),
)
LED_SWITCH_DRIVER_FOOTPRINT = footprint(
    "SOT-23 (TO-236)",
    "BSS138LT1G N-channel MOSFET",
    LED_SWITCH_DRIVER_PADS,
    courtyard_for(LED_SWITCH_DRIVER_PADS, (2.9, 2.4)),
)
add_polarity_marker(LED_SWITCH_DRIVER_FOOTPRINT, "1")

# TI SN74LVC1G97 DBV0006A example board layout (4214840/G, SCES416N p36): six
# 1.1 x 0.6 pads at 0.95 pitch, columns 2.6 apart; pins 1-3 down one side, 4-6 up
# the other (counter-clockwise from pin 1).
LED_ENABLE_GATE_FOOTPRINT = soic(
    "SOT-23-6 (DBV)",
    "SN74LVC1G97 configurable gate",
    6,
    2.6,
    (3.0, 3.05),
    tuple(LogicGatePin),
    pin_pitch_mm=0.95,
    pad_size_mm=(1.1, 0.6),
)
add_polarity_marker(LED_ENABLE_GATE_FOOTPRINT, "1")

LED_SWITCH_PART = PcbPart(
    LED_SWITCH,
    PowerMosfet,
    LED_SWITCH_FOOTPRINT,
    "Q_PMOS",
    "Si4403DDY",
    "LED rail switch, +5V to LED_5V",
    DrawingView.MOUNTING_SIDE,
)
LED_SWITCH_DRIVER_PART = PcbPart(
    LED_SWITCH_DRIVER,
    SmallMosfet,
    LED_SWITCH_DRIVER_FOOTPRINT,
    "Q_NMOS",
    "BSS138LT1G",
    "LED_EN inverter driving the LED switch gate and buffer enables",
    DrawingView.MOUNTING_SIDE,
)
LED_ENABLE_GATE_PART = PcbPart(
    LED_ENABLE_GATE,
    LogicGate,
    LED_ENABLE_GATE_FOOTPRINT,
    "LVC1G97",
    "SN74LVC1G97",
    "LED_OE_N = Schmitt(Q1 gate) OR LED_EN_N: buffer on only once LED_5V is up",
    DrawingView.MOUNTING_SIDE,
)
