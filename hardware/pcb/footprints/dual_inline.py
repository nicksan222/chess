"""DIP packages, and the sockets that share their pads.

A socket is not a separate footprint. It occupies exactly the pads its chip would
have occupied, so `DIP-14` and `DIP-28` resolve to the same geometry as the chips
they hold. The placement module skips the socket references for that reason: two
footprints on one set of holes would double every pad.
"""

from __future__ import annotations

from .base import dual_inline

PDIP_28 = dual_inline(
    "PDIP-28",
    "MCP23017 I2C port expander",
    ways=28,
    row_spacing=7.62,
)

DIP_28_SOCKET = dual_inline(
    "DIP-28",
    "28-pin socket; shares the pads of the chip it holds",
    ways=28,
    row_spacing=7.62,
)

DIP_14 = dual_inline(
    "DIP-14",
    "SN74AHCT125N quad buffer, and its socket",
    ways=14,
    row_spacing=7.62,
)
