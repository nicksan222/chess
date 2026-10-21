"""The mechanical interface the PCB publishes to the enclosure.

Written into `generated/pcb-components.json` beside the parts list. It carries the
board facts the case and plate are built from: the grid and its square features,
the outline and mounting holes, the Pi hanging from J1, the panel products wired to
the board and the off-board harness. It is derived data computed from `pcb.spec`,
never an editable source, and must stay readable by Blender's Python 3.11 without
KiCad: `pcb.spec` is imported only inside `current()`.

All positions are board millimetres: origin at the playing-area centre, Y up, seen
from the PCB top. The CAD build refuses an export older than these sources, so
reading only rebuilds the dataclasses from the JSON `asdict` wrote.
"""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from types import NoneType, UnionType
from typing import cast, get_args, get_origin, get_type_hints

Point = tuple[float, float]
Size2 = tuple[float, float]
Size3 = tuple[float, float, float]


def decode(kind: object, value: object) -> object:
    """Rebuild a value of type `kind` from its `asdict` JSON form."""
    if isinstance(kind, type) and is_dataclass(kind):
        hints = cast(dict[str, object], get_type_hints(kind))
        data = cast(dict[str, object], value)
        if unknown := sorted(set(data) - set(hints)):
            raise ValueError(f"{kind.__name__} has no fields {unknown}")
        return kind(**{name: decode(hints[name], item) for name, item in data.items()})
    args = cast(tuple[object, ...], get_args(kind))
    origin = get_origin(kind)
    if origin is UnionType:
        if value is None and NoneType in args:
            return None
        (inner,) = (arg for arg in args if arg is not NoneType)
        return decode(inner, value)
    if origin is tuple:
        items = cast(list[object], value)
        if args[-1] is Ellipsis:
            return tuple(decode(args[0], item) for item in items)
        if len(items) != len(args):
            raise ValueError(f"expected {len(args)} values, got {items!r}")
        return tuple(decode(arg, item) for arg, item in zip(args, items, strict=True))
    if origin is dict:
        mapping = cast(dict[str, object], value)
        return {key: decode(args[1], item) for key, item in mapping.items()}
    if kind is float and type(value) is int:
        return float(value)
    if not isinstance(kind, type) or not isinstance(value, kind):
        raise ValueError(f"expected {kind!r}, got {value!r}")
    return value


@dataclass(frozen=True)
class SquareSite:
    """One playing square: identity, colour and where its LED and sensor sit."""

    name: str
    row: int  # Counted from the top of the board (rank 8 is row 0), as drawn.
    column: int  # Counted from file A.
    is_dark: bool
    centre_mm: Point
    led_position_mm: Point
    hall_position_mm: Point


@dataclass(frozen=True)
class HostSite:
    """The Pi Zero 2 W as it hangs, component side up, from header J1.

    `rotation_degrees` turns the Pi's own drawing view (RP-008358-DS-1: header along
    the top edge, microSD at the left) about Z, seen from the PCB top and never
    mirrored. It is not J1's footprint rotation, which the parts list carries.
    """

    board_mm: Size3  # Drawing-frame length, width and PCB thickness.
    centre_mm: Point
    rotation_degrees: float
    board_to_board_mm: float  # Main PCB underside to the Pi's top face.
    header_height_mm: float  # The socket on the main PCB alone.
    sd_socket_mm: Point
    sd_socket_height_mm: float
    # Field names above that rest on a measured view rather than a dimensioned
    # drawing; the enclosure must treat them as provisional.
    unverified: tuple[str, ...]


@dataclass(frozen=True)
class DisplayModule:
    """MC242GW module geometry from its supplier drawing, in module coordinates."""

    body_mm: Size3
    screen_mm: Size2
    screen_offset_mm: Point
    mount_holes_mm: tuple[Point, ...]
    mount_hole_diameter_mm: float
    underside_mm: Size3
    pads_mm: dict[str, Point]  # Silkscreen label to pad centre.
    pcb_thickness_mm: float
    frame_mm: Size3


@dataclass(frozen=True)
class PanelJack:
    """Switchcraft 722A geometry from drawing "712A 722A 732A" rev J."""

    body_mm: Size3  # Behind the flange to the lug ends, by the flange diameter.
    bushing_diameter_mm: float
    thread_length_mm: float
    flange_diameter_mm: float
    max_panel_mm: float


@dataclass(frozen=True)
class RockerSwitch:
    """RA11131100 geometry from drawing 38-RA11131100 rev D."""

    body_mm: Size3
    face_mm: Size3
    cutout_mm: Size2
    panel_range_mm: Size2
    terminal_length_mm: float
    terminal_pitch_mm: float
    terminal_width_mm: float
    terminal_thickness_mm: float


@dataclass(frozen=True)
class HarnessRun:
    """One off-board wire: the header cavity it is crimped into and its far end."""

    harness: str  # The named harness it belongs to, e.g. "OLED".
    connector: str
    cavity: str
    net: str
    colour: str
    gauge_awg: int
    length_mm: float  # Cut length, service slack included.
    outside_diameter_mm: float
    far_part: str  # Approved product key at the far end.
    far_terminal: str  # Terminal label there, as the part's drawing names it.
    far_termination: str  # How the wire is attached at the far end.


@dataclass(frozen=True)
class BoardInterface:
    """Everything the enclosure needs to know about the board, in board mm."""

    grid_count: int
    square_size_mm: float
    playing_span_mm: float
    panel_strip_depth_mm: float
    panel_origin_y_mm: float  # Centre line of the control strip.
    pcb_size_mm: Size3  # Width, depth and thickness of the bare board.
    # Where the PCB outline's centre sits in board coordinates (Y only); it is
    # off the playing-area centre because the control strip hangs off the front.
    pcb_center_offset_y_mm: float
    bottom_edge_keepout_mm: float  # No underside part this close to the edge.
    squares: tuple[SquareSite, ...]
    led_offset_mm: Point  # LED centre relative to its square centre.
    led_package_max_mm: Size3  # Nominal package plus its tolerance.
    led_package_tolerance_mm: float
    led_emitter_window_mm: Size2
    hall_sensor_mm: Size3
    hall_sensor_standoff_mm: float
    expander_mm: Size3  # As placed: X along the board, Y across it.
    expanders_mm: dict[str, Point]  # Hall-bank label to centre.
    mounting_holes_mm: tuple[Point, ...]
    mounting_hole_diameter_mm: float
    button_actuator_diameter_mm: float
    host: HostSite
    display: DisplayModule
    jack: PanelJack
    rocker: RockerSwitch
    harness: tuple[HarnessRun, ...]

    @classmethod
    def current(cls) -> BoardInterface:
        """Compute the interface from the PCB specification (host Python only)."""
        from pcb.spec import host, layout
        from pcb.spec.components import BARREL_JACK, OLED_MODULE
        from pcb.spec.components import barrel_jack as jack
        from pcb.spec.components import button as button_part
        from pcb.spec.components import oled_module as oled
        from pcb.spec.components import power_switch as rocker
        from pcb.spec.components.harness import WIRE_OUTSIDE_DIAMETERS_MM
        from pcb.spec.electronics.harness import HARNESSES

        host_fields = {
            "PI_SD_SOCKET_ON_PI_MM": "sd_socket_mm",
            "PI_SD_SOCKET_HEIGHT_MM": "sd_socket_height_mm",
        }
        led_x, led_y, led_z = layout.LED_PACKAGE_MAX_SIZE_MM
        return cls(
            layout.GRID_COUNT,
            layout.SQUARE_SIZE_MM,
            layout.PLAYING_SPAN_MM,
            layout.PANEL_STRIP_DEPTH_MM,
            layout.PANEL_ORIGIN_Y_MM,
            layout.PCB_SIZE_MM,
            layout.PCB_CENTER_OFFSET_Y_MM,
            layout.PCB_BOTTOM_EDGE_KEEPOUT_MM,
            tuple(
                SquareSite(
                    square.name,
                    square.row,
                    square.column,
                    square.is_dark,
                    square.centre_mm,
                    square.led_position_mm,
                    square.hall_position_mm,
                )
                for square in layout.BOARD_SQUARES
            ),
            layout.LED_POSITION_MM,
            (led_x, led_y, led_z),
            layout.LED_PACKAGE_TOLERANCE_MM,
            layout.LED_EMITTER_WINDOW_MM,
            layout.HALL_SENSOR_PACKAGE_MM,
            layout.HALL_SENSOR_STANDOFF_MM,
            layout.EXPANDER_BODY_MM,
            {
                label: (x, y)
                for label, (x, y) in layout.EXPANDER_POSITIONS_BY_BANK_MM.items()
            },
            layout.PCB_MOUNTING_HOLE_POSITIONS_MM,
            layout.PCB_MOUNTING_HOLE_DIAMETER_MM,
            button_part.BUTTON_ACTUATOR_DIAMETER_MM,
            HostSite(
                host.PI_BOARD_SIZE_MM,
                host.PI_CENTER_MM,
                host.PI_ROTATION_DEG,
                host.PI_BOARD_TO_BOARD_MM,
                host.PI_HEADER_HEIGHT_MM,
                host.PI_SD_SOCKET_MM,
                host.PI_SD_SOCKET_HEIGHT_MM,
                tuple(host_fields[name] for name in host.UNVERIFIED_HOST_DIMENSIONS),
            ),
            DisplayModule(
                OLED_MODULE.require_body_mm(),
                oled.OLED_SCREEN_SIZE_MM,
                oled.OLED_SCREEN_OFFSET_MM,
                oled.OLED_MOUNT_HOLES_MM,
                oled.OLED_MOUNT_HOLE_DIAMETER_MM,
                oled.OLED_UNDERSIDE_SIZE_MM,
                dict(
                    zip(oled.OLED_PAD_LABELS, oled.OLED_PAD_POSITIONS_MM, strict=True)
                ),
                oled.OLED_PCB_THICKNESS_MM,
                oled.OLED_FRAME_MM,
            ),
            PanelJack(
                BARREL_JACK.require_body_mm(),
                jack.JACK_BUSHING_DIAMETER_MM,
                jack.JACK_THREAD_LENGTH_MM,
                jack.JACK_FLANGE_DIAMETER_MM,
                jack.JACK_MAX_PANEL_MM,
            ),
            RockerSwitch(
                rocker.ROCKER_BODY_MM,
                rocker.ROCKER_FACE_MM,
                rocker.ROCKER_CUTOUT_MM,
                rocker.ROCKER_PANEL_RANGE_MM,
                rocker.ROCKER_TERMINAL_LENGTH_MM,
                rocker.ROCKER_TERMINAL_PITCH_MM,
                rocker.ROCKER_TERMINAL_WIDTH_MM,
                rocker.ROCKER_TERMINAL_THICKNESS_MM,
            ),
            tuple(
                HarnessRun(
                    name,
                    wire.connector,
                    str(wire.cavity),
                    wire.net,
                    wire.colour,
                    wire.gauge_awg,
                    wire.length_mm,
                    WIRE_OUTSIDE_DIAMETERS_MM[wire.gauge_awg],
                    wire.far_part,
                    str(wire.far_terminal),
                    wire.far_termination,
                )
                for name, wires in HARNESSES.items()
                for wire in wires
            ),
        )
