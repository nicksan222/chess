"""Approved product: Yageo 56 ohm 0603 resistor (LED data source termination, R9).

S5: U5's AHCT125 output (SCLS264R VOH/VOL slopes about 75/43 ohm) drives the first
LED_DATA link on B.Cu (about 102 ohm, IPC-2141 on the PCBWay stackup). 56 ohm in
series keeps U6's input inside SK9822 §7 -0.3..VDD+0.3 V at the edge-rate corners.
"""

from .spec import part

RES_56 = part(
    "RES_56",
    "56 ohm 1 % 0.1 W thick-film resistor",
    "0603 (1608 metric)",
    "Yageo",
    "RC0603FR-0756RL",
    (1.6, 0.8, 0.55),
    datasheet="https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L",
)
