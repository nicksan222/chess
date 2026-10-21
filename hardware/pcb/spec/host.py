"""Where the Raspberry Pi Zero 2 W hangs under the board, and its header stack.

Role: the PCB places header J1 from `PI_HEADER_CENTER_MM` and `PI_ROTATION_DEG`; the
Pi plugs up into it, so the Pi's position is a consequence of that placement. Pi
board facts come from drawing RP-008358-DS-1. The PCB exports the derived centre,
outline, stack height and microSD socket position; the case builds its bay, vents
and card slot from that export. Coordinates are board millimetres, origin at the
playing-area centre, Y up, seen from the PCB top.
"""

from types import MappingProxyType

from pcb.spec.components import PI_ZERO_2_W

from .layout import (
    PCB_CENTER_OFFSET_Y_MM,
    PCB_MOUNTING_HOLE_DIAMETER_MM,
    PCB_MOUNTING_HOLE_POSITIONS_MM,
    PCB_SIZE_MM,
)

# Raspberry Pi Zero 2 W hangs component side up under the board, its male
# header plugged up into J1 on the PCB bottom. Seen from the PCB top it is the
# RP-008358-DS-1 drawing view, rotated but never mirrored. Drawing frame: origin
# at the Pi's bottom-left corner, header along the top edge, microSD at the left.
PI_BOARD_SIZE_MM = (*PI_ZERO_2_W.require_body_mm()[:2], 1.4)
# Header centre: left hole (3.5) + 29 along X, on the hole line 3.5 below the top.
PI_HEADER_ON_PI_MM = (32.5, PI_BOARD_SIZE_MM[1] - 3.5)
PI_HEADER_PITCH_MM = 2.54
PI_HEADER_PIN_COUNT = 40
# Board placement: the header centre is the one anchor; everything else derives.
PI_HEADER_CENTER_MM = (123.0, -75.0)
PI_ROTATION_DEG = 180.0
# Stack: Sullins PPPC202LFBN-RC insulator .334 in (8.50) on the PCB plus the
# PRPC020DAAN-RC insulator .100 in (2.54) on the Pi.
PI_HEADER_HEIGHT_MM = 8.5
PI_MALE_HEADER_INSULATOR_MM = 2.54
PI_BOARD_TO_BOARD_MM = PI_HEADER_HEIGHT_MM + PI_MALE_HEADER_INSULATOR_MM
PI_HEADER_BODY_MM = (51.0, 5.0, PI_HEADER_HEIGHT_MM)
# microSD socket centre in the drawing frame, measured from the rendered
# RP-008358-DS-1 view (the drawing does not dimension it); the card enters from
# the Pi's left edge, on its top face, which faces the PCB here.
PI_SD_SOCKET_ON_PI_MM = (7.4, 16.85)
PI_SD_SOCKET_HEIGHT_MM = 1.4
# Host values still resting on a measured view rather than a dimensioned drawing.
# Each must be cleared by a citation or a physical measurement before release.
UNVERIFIED_HOST_DIMENSIONS = MappingProxyType(
    {
        "PI_SD_SOCKET_ON_PI_MM": (
            "microSD socket centre measured from the rendered RP-008358-DS-1 "
            "view; the drawing does not dimension it."
        ),
        "PI_SD_SOCKET_HEIGHT_MM": (
            "microSD socket height on the Pi Zero 2 W assumed (1.4 mm); sets the "
            "case slot height."
        ),
    }
)

# The Pi is only ever placed at multiples of 90 degrees, so rotation is done exactly
# with these cos/sin pairs instead of floating-point trigonometry.
_QUARTER_TURNS = {0: (1.0, 0.0), 90: (0.0, 1.0), 180: (-1.0, 0.0), 270: (0.0, -1.0)}


def _rotate(vector: tuple[float, float], degrees: float) -> tuple[float, float]:
    """Exact rotation by a quarter turn, which is all a placement here uses."""
    cos, sin = _QUARTER_TURNS[int(degrees) % 360]
    return (vector[0] * cos - vector[1] * sin, vector[0] * sin + vector[1] * cos)


def pi_on_board_xy(point_on_pi: tuple[float, float]) -> tuple[float, float]:
    """Board XY, seen from the PCB top, of a point in the Pi drawing frame."""
    dx, dy = _rotate(
        (
            point_on_pi[0] - PI_HEADER_ON_PI_MM[0],
            point_on_pi[1] - PI_HEADER_ON_PI_MM[1],
        ),
        PI_ROTATION_DEG,
    )
    return (PI_HEADER_CENTER_MM[0] + dx, PI_HEADER_CENTER_MM[1] + dy)


def pi_header_pin_xy(pin: int) -> tuple[float, float]:
    """Board XY, seen from the PCB top, of Pi GPIO header pin 1..40.

    Pin 1 is the square pad at the microSD end of the inner row; odd pins run
    along the inner row and even pins along the outer row, at the board edge.
    """
    if not 1 <= pin <= PI_HEADER_PIN_COUNT:
        raise ValueError(f"Pi header pin {pin} is outside 1..{PI_HEADER_PIN_COUNT}")
    column = (pin - 1) // 2
    half_rows = PI_HEADER_PITCH_MM / 2.0
    return pi_on_board_xy(
        (
            PI_HEADER_ON_PI_MM[0] + (column - 9.5) * PI_HEADER_PITCH_MM,
            PI_HEADER_ON_PI_MM[1] + (half_rows if pin % 2 == 0 else -half_rows),
        )
    )


# Pi board centre in board coordinates, derived from the header anchor.
PI_CENTER_MM = pi_on_board_xy((PI_BOARD_SIZE_MM[0] / 2.0, PI_BOARD_SIZE_MM[1] / 2.0))
PI_SD_SOCKET_MM = pi_on_board_xy(PI_SD_SOCKET_ON_PI_MM)


def _outside(
    point: tuple[float, float], centre: tuple[float, float], size: tuple[float, float]
) -> float:
    """Distance outside an axis-aligned rectangle; negative means inside."""
    return max(
        abs(point[0] - centre[0]) - size[0] / 2.0,
        abs(point[1] - centre[1]) - size[1] / 2.0,
    )


def validate() -> None:
    """The header lands on the Pi, and the Pi hangs entirely under the board."""
    if int(PI_ROTATION_DEG) % 90:
        raise ValueError("The Pi placement must be a quarter-turn rotation")
    turned = int(PI_ROTATION_DEG) % 180 == 90
    size = (
        (PI_BOARD_SIZE_MM[1], PI_BOARD_SIZE_MM[0]) if turned else PI_BOARD_SIZE_MM[:2]
    )
    pins = [pi_header_pin_xy(pin) for pin in range(1, PI_HEADER_PIN_COUNT + 1)]
    if any(_outside(pin, PI_CENTER_MM, size) > 0.0 for pin in pins):
        raise ValueError("A Pi header pin lands outside the Pi")
    board_centre = (0.0, PCB_CENTER_OFFSET_Y_MM)
    if _outside(PI_CENTER_MM, board_centre, PCB_SIZE_MM[:2]) > -max(size) / 2.0:
        raise ValueError("The Pi does not hang entirely under the board")
    if _outside(PI_SD_SOCKET_MM, PI_CENTER_MM, size) > 0.0:
        raise ValueError("The microSD socket is not on the Pi")
    hole_radius = PCB_MOUNTING_HOLE_DIAMETER_MM / 2.0
    for hole in PCB_MOUNTING_HOLE_POSITIONS_MM:
        if _outside(hole, PI_CENTER_MM, size) < hole_radius:
            raise ValueError("A mounting hole lands over the Pi")


validate()
