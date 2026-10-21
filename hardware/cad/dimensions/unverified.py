"""Enclosure dimensions still resting on an unread datasheet or a measured drawing.

Each entry must be cleared by a citation or a physical measurement before release,
not here. Each key must name a real dimension constant (a test enforces it), and the
reason says what is missing and how to close it. Host values the PCB exports as
provisional (the Pi's microSD socket) are added from the export, so the slot built
from them is flagged too.
"""

from types import MappingProxyType

from .board import BOARD

# Exported host field -> the enclosure constant built from it.
_HOST_FIELDS = {
    "sd_socket_mm": "PI_SD_SOCKET_MM",
    "sd_socket_height_mm": "PI_SD_SOCKET_HEIGHT_MM",
}

UNVERIFIED_DIMENSIONS = MappingProxyType(
    {
        **{
            _HOST_FIELDS[field]: (
                f"The PCB exports host `{field}` as provisional: it rests on a "
                "measured view of RP-008358-DS-1, not a dimension; it sets the "
                "case microSD slot."
            )
            for field in BOARD.host.unverified
        },
        "CASE_ROCKER_BAY_DEPTH_MM": (
            "Rocker body and tabs reach 18.5 +/- 1.0 mm behind the panel (E-Switch "
            "RA1 sheet p2); the two TE 2-520275-2 receptacles and wire exit are "
            "not drawn. 50.5 mm reserved."
        ),
        "CASE_JACK_BAY_DEPTH_MM": (
            "722A body and lugs reach 15.3 mm behind the panel (drawing 20.8 - "
            "5.46); 30 mm reserved for the soldered 18 AWG wires and their bend."
        ),
    }
)
