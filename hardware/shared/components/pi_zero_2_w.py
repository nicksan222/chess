"""Approved product: Raspberry Pi Zero 2 W host (off-board, human BOM only).

It plugs onto header J1; the single Linux process in `apps/firmware` runs on it.
"""

from .spec import part

PI_ZERO_2_W = part(
    "PI_ZERO_2_W",
    "Raspberry Pi Zero 2 W host",
    "65x30 mm module",
    "Raspberry Pi",
    "SC0510",
    (65.0, 30.0, 5.2),
)
