"""DIP packages and sockets, sized from approved product bodies."""

from __future__ import annotations

from .base import dual_inline

PDIP_28 = dual_inline(
    "PDIP-28",
    "MCP23017-E/SP I2C port expander",
    ways=28,
    row_spacing=7.62,
    body=(7.6, 34.8),
)

DIP_28_SOCKET = dual_inline(
    "DIP-28",
    "Mill-Max 110-44-628-41-001000 socket",
    ways=28,
    row_spacing=7.62,
    body=(7.6, 34.8),
)

DIP_14 = dual_inline(
    "DIP-14",
    "SN74AHCT125N and Mill-Max 110-44-314-41-001000 socket",
    ways=14,
    row_spacing=7.62,
    body=(6.35, 19.3),
)
