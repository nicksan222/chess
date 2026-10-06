"""Approved products: the LED rail switch (user decision D1, interface H5).

Q1 Vishay Si4403DDY (S17-0318-Rev A): P-channel, VDS -20 V, VGS +-8 V, RDS(on)
14.0 mOhm max / 10.5 typ at VGS -4.5 V, ID -10.9 A at TA 25 C, SO-8 (pins 1-3
source, 4 gate, 5-8 drain). -20 V tolerates the +5V running-step residual (S4c).
Q2 onsemi BSS138LT1G (BSS138LT1/D Rev 15, Sept 2026): N-channel, 50 V, VGS +-20 V, VGS(th)
0.85-1.5 V, rDS(on) 10 Ohm max at VGS 2.75 V, SOT-23 STYLE 21 (1 gate, 2 source,
3 drain): the Pi's 3.3 V LED_EN switches it fully.
U75 TI SN74LVC1G97DBVR (SCES416N; S6b H6): configurable gate with Schmitt inputs
(VT+ 2.16-3.33 V, VT- 1.41-2.29 V at VCC 4.5-5.5 V), wired as an OR that holds the
AHCT125 outputs off until Q1 is fully on. On +5V (5.66 V steady at the OVLO trip,
6.02 V during the S4c running step) it stays inside VCC and VI -0.5..6.5 V (6.1).
"""

from .spec import part

LED_SWITCH = part(
    "LED_SWITCH",
    "-20 V 14 mOhm P-channel MOSFET (LED rail switch)",
    "SO-8 1.27 mm",
    "Vishay Siliconix",
    "Si4403DDY-T1-GE3",
    (4.9, 6.0, 1.75),  # D x H (lead span) x A, package information 71192.
    "https://www.vishay.com/docs/70094/si4403ddy.pdf",
)
LED_SWITCH_DRIVER = part(
    "LED_SWITCH_DRIVER",
    "50 V logic-level N-channel MOSFET (LED switch driver)",
    "SOT-23 (TO-236)",
    "onsemi",
    "BSS138LT1G",
    (2.9, 2.4, 1.0),  # D x HE x A, case 318 Issue AU.
    "https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf",  # Rev 15
)
LED_ENABLE_GATE = part(
    "LED_ENABLE_GATE",
    "Configurable gate with Schmitt inputs (LED buffer enable)",
    "SOT-23-6 (DBV)",
    "Texas Instruments",
    "SN74LVC1G97DBVR",
    (3.05, 3.0, 1.45),  # D x lead span x height, DBV0006A (4214840/G).
    "https://www.ti.com/lit/ds/symlink/sn74lvc1g97.pdf",
)
