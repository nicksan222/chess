"""Dimensions still resting on an unread datasheet or a measured drawing.

The PCB release gate imports this list into its ASSUMPTIONS, so each entry must
be cleared by a citation or a physical measurement before release, not here.
Each key must name a real dimension constant (a shared test enforces it), and the reason
says what is missing and how to close it.
"""

from types import MappingProxyType

UNVERIFIED_DIMENSIONS = MappingProxyType(
    {
        "CASE_ROCKER_BAY_DEPTH_MM": (
            "Rocker body and tabs reach 18.5 +/- 1.0 mm behind the panel (E-Switch "
            "RA1 sheet p2); the two TE 2-520275-2 receptacles and wire exit are "
            "not drawn. 50.5 mm reserved."
        ),
        "CASE_JACK_BAY_DEPTH_MM": (
            "722A body and lugs reach 15.3 mm behind the panel (drawing 20.8 - "
            "5.46); 30 mm reserved for the soldered 18 AWG wires and their bend."
        ),
        "PI_SD_SOCKET_ON_PI_MM": (
            "microSD socket centre measured from the rendered RP-008358-DS-1 "
            "view; the drawing does not dimension it."
        ),
        "PI_SD_SOCKET_HEIGHT_MM": (
            "microSD socket height on the Pi Zero 2 W assumed (1.4 mm); sets the "
            "slot height."
        ),
    }
)
