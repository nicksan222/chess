"""Approved product: the board's wire-to-board power-entry header."""

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
