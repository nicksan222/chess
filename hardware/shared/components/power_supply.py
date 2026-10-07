"""Approved product: Mean Well GST18A05-P1J 5 V 3 A supply (off-board, human BOM only).

This external supply feeds the board's DC input. The board retains its 2 A
fuse and operating budget; the adapter rating does not raise either limit.
"""

from .spec import part

POWER_SUPPLY = part(
    "POWER_SUPPLY",
    "5 V 3 A regulated desktop supply with 5.5x2.1 mm plug",
    "external PSU",
    "MEAN WELL",
    "GST18A05-P1J",
    datasheet="https://www.meanwell.com/Upload/PDF/GST18A/GST18A-SPEC.PDF",
)

POWER_SUPPLY_OUTPUT_VOLTS = 5.0
POWER_SUPPLY_RATED_AMPERES = 3.0
