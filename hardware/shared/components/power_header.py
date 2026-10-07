"""Approved product: the board's wire-to-board power-entry header."""

from typing import Literal

from .spec import part

# JST VH catalogue (eVH.pdf) pp1-4: B4PS-VH side entry, 3.96 mm pitch, 10 A with
# AWG #16 / 7 A with AWG #18 per contact, positive lock; body B 15.78 x 10.9 deep,
# 8.5 high; mates VHR-4N with SVH-21T-P1.1 contacts.
POWER_HEADER = part(
    "POWER_HEADER",
    "4-pin 3.96 mm locking side-entry power-entry header",
    "VH 4P side entry THT",
    "JST",
    "B4PS-VH",
    (15.78, 10.9, 8.5),
    "https://www.jst-mfg.com/product/pdf/eng/eVH.pdf",
)

# Local -Y start/end, width, height and role of the mated housing and wire exit.
POWER_HEADER_MATED_ZONES: tuple[
    tuple[float, float, float, float, Literal["housing", "wire_exit"]], ...
] = (
    (-5.45, 16.05, 15.8, 10.5, "housing"),
    (16.05, 19.55, 15.8, 10.5, "wire_exit"),
)
