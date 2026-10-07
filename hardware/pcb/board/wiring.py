"""Readable copper choices. Components already own the electrical connections."""

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING

from pcb.board.board import BoardNet
from pcb.harness import (
    Bend,
    CopperLayer,
    CopperPath,
    DirectLink,
    Net,
    NetRoute,
    PinLaunch,
    Point,
    RouteStage,
    RoutingPlan,
    Via,
)
from pcb.harness.components.capacitor import CapacitorPin
from pcb.harness.components.resistor import ResistorPin
from shared import dimensions
from shared.electronics import (
    FusePin,
    PowerHeaderPin,
    Sk9822Pin,
)
from shared.electronics.ahct125 import Ahct125Pin
from shared.electronics.efuse import EfusePin
from shared.electronics.hall_sensor import HallSensorPin
from shared.electronics.passives import TvsDiodePin
from shared.hall_banks import BANK_FILES, BANK_RANKS
from shared.panel_buttons import PANEL_BUTTONS

if TYPE_CHECKING:
    from pcb.board.board import Board

TOP = CopperLayer.TOP
BOTTOM = CopperLayer.BOTTOM
INNER_SIGNALS = (CopperLayer.INNER_4, CopperLayer.INNER_5)
SIGNALS = (TOP, BOTTOM, *INNER_SIGNALS)


def wiring(board: Board) -> tuple[NetRoute, ...]:
    controls = tuple(
        NetRoute(
            net,
            layers=SIGNALS
            if net in (BoardNet.LED_EN, BoardNet.LED_OE_N)
            else (TOP, BOTTOM),
            prune_unused_vias=True,
            reserve_group=True,
        )
        for net in sorted(
            (
                BoardNet.SPI_CLK_3V3,
                BoardNet.SPI_DATA_3V3,
                BoardNet.LED_CLK_5V,
                BoardNet.LED_DATA_5V,
                BoardNet.LED_EN,
                BoardNet.LED_EN_N,
                BoardNet.LED_EN_GATE,
                BoardNet.LED_SW_GATE,
                BoardNet.LED_OE_N,
            ),
            key=lambda net: net.label,
        )
    )
    buttons = tuple(
        NetRoute(
            BoardNet(button.net_name),
            preferred_layer=BOTTOM if index % 2 == 0 else TOP,
            priority=1,
            launch=PinLaunch(
                board.host_header.reference,
                fallback_layers=tuple(
                    INNER_SIGNALS[
                        (button.fallback_layer_index + offset) % len(INNER_SIGNALS)
                    ]
                    for offset in range(len(INNER_SIGNALS))
                ),
                x_offset_mm=button.header_launch_x_offset_mm,
            ),
        )
        for index, button in enumerate(PANEL_BUTTONS.routing_order)
    )
    # Reserve I2C package escape vias before the long button routes can occupy them.
    buses = (
        NetRoute(
            BoardNet.I2C_SDA,
            layers=INNER_SIGNALS,
            preferred_layer=CopperLayer.INNER_4,
            priority=2,
            reserve_group=True,
        ),
        NetRoute(
            BoardNet.I2C_SCL,
            layers=INNER_SIGNALS,
            preferred_layer=CopperLayer.INNER_5,
            priority=2,
            reserve_group=True,
        ),
    )
    sensors: list[NetRoute] = []
    # A loop writes the repeated intent; every sensor is still a separate instance.
    for bank in dimensions.HALL_BANKS:
        x, y = bank.centre(dimensions.SQUARE_SIZE_MM, dimensions.PLAYING_SPAN_MM)
        y += (dimensions.PCB_SIZE_MM[1] - dimensions.PLAYING_SPAN_MM) / 2
        half_width = BANK_FILES * dimensions.SQUARE_SIZE_MM / 2 - 1
        half_height = BANK_RANKS * dimensions.SQUARE_SIZE_MM / 2 - 1
        area = (x - half_width, y - half_height, x + half_width, y + half_height)
        for square in bank.members:
            sensor = board.sensors[square.name]
            sensors.append(
                NetRoute(
                    sensor.net(HallSensorPin.ACTIVE_LOW_OUTPUT),
                    layers=SIGNALS,
                    area=area,
                    diagonals=True,
                    prune_unused_vias=True,
                    priority=3,
                )
            )
    return (*controls, *buttons, *buses, *sensors)


def power_paths(board: Board) -> tuple[CopperPath, ...]:
    return (
        CopperPath(
            BoardNet.DC_IN,
            (
                board.power_connector.endpoint(PowerHeaderPin.DC_INPUT),
                board.input_fuse.endpoint(FusePin.UNFUSED_INPUT),
            ),
            width_mm=1.5,
            bend=Bend.VERTICAL_FIRST,
        ),
        CopperPath(
            BoardNet.DC_FUSED,
            (
                board.power_connector.endpoint(PowerHeaderPin.FUSED_TO_SWITCH),
                board.input_fuse.endpoint(FusePin.FUSED_OUTPUT),
            ),
            width_mm=1.5,
            bend=Bend.VERTICAL_FIRST,
        ),
    )


def power_copper(board: Board) -> RouteStage:
    """Connect the fuse's package ports to its real surrounding components."""
    fuse = board.electronic_fuse
    top, bottom = fuse.port("input_north"), fuse.port("input_south")
    connector = board.power_connector.pin_position(PowerHeaderPin.FUSED_TO_SWITCH)
    input_net = fuse.net(EfusePin.INPUT)
    paths = list(power_paths(board))
    paths.extend(
        CopperPath(input_net, (port, Point(connector.x_mm, port.y_mm)), width_mm=1.5)
        for port in (top, bottom)
    )
    paths.append(
        CopperPath(
            input_net, (connector, Point(connector.x_mm, top.y_mm)), width_mm=1.5
        )
    )
    vias: list[Via[Net]] = []
    for pin, port, endpoint, width in (
        (
            EfusePin.OVERCURRENT_TIMER,
            "timer",
            board.timer_capacitor.endpoint(CapacitorPin.TERMINAL_A),
            0.31,
        ),
        (
            EfusePin.CURRENT_LIMIT,
            "current_limit",
            board.current_limit_resistor.endpoint(ResistorPin.TERMINAL_A),
            0.2,
        ),
        (
            EfusePin.GROUND,
            "ground",
            board.current_limit_resistor.endpoint(ResistorPin.TERMINAL_B),
            0.2,
        ),
        (
            EfusePin.SLEW_RATE,
            "slew_rate",
            board.slew_capacitor.endpoint(CapacitorPin.TERMINAL_A),
            0.31,
        ),
    ):
        paths.append(
            CopperPath(fuse.net(pin), (fuse.port(port), endpoint), width_mm=width)
        )
    ground = fuse.net(EfusePin.GROUND)
    shared_ground = fuse.local_point(4.5, -2.2)
    timer_ground = fuse.local_point(5.45, 2.4)
    paths.extend(
        (
            CopperPath(
                ground,
                (
                    board.current_limit_resistor.endpoint(ResistorPin.TERMINAL_B),
                    board.slew_capacitor.endpoint(CapacitorPin.TERMINAL_B),
                    shared_ground,
                ),
            ),
            CopperPath(
                ground,
                (board.timer_capacitor.endpoint(CapacitorPin.TERMINAL_B), timer_ground),
            ),
            CopperPath(
                ground,
                (
                    board.overvoltage_filter.endpoint(CapacitorPin.TERMINAL_B),
                    board.slew_capacitor.endpoint(CapacitorPin.TERMINAL_B),
                ),
            ),
        )
    )
    vias.extend(Via(ground, point, 0.9, 0.4) for point in (shared_ground, timer_ground))
    overvoltage = board.overvoltage_top.pin_position(ResistorPin.TERMINAL_A)
    junction = fuse.port("overvoltage")
    midpoint = Point(
        (junction.x_mm + overvoltage.x_mm) / 2, (junction.y_mm + overvoltage.y_mm) / 2
    )
    paths.append(
        CopperPath(
            fuse.net(EfusePin.OVERVOLTAGE_LOCKOUT),
            (
                junction,
                midpoint,
                board.overvoltage_top.endpoint(ResistorPin.TERMINAL_A),
            ),
        )
    )
    vias.append(Via(fuse.net(EfusePin.OVERVOLTAGE_LOCKOUT), midpoint, 0.9, 0.4))
    for endpoint, pad, port in (
        (
            board.overvoltage_top.endpoint(ResistorPin.TERMINAL_B),
            board.overvoltage_top.pin_position(ResistorPin.TERMINAL_B),
            bottom,
        ),
        (
            board.input_bypass.endpoint(CapacitorPin.TERMINAL_A),
            board.input_bypass.pin_position(CapacitorPin.TERMINAL_A),
            top,
        ),
    ):
        paths.append(CopperPath(input_net, (endpoint, Point(pad.x_mm, port.y_mm))))
    tvs = board.input_tvs.pin_position(TvsDiodePin.PROTECTED_INPUT)
    paths.append(
        CopperPath(
            input_net,
            (
                board.input_tvs.endpoint(TvsDiodePin.PROTECTED_INPUT),
                Point(connector.x_mm, tvs.y_mm),
            ),
            width_mm=1.0,
        )
    )
    return RouteStage(paths=tuple(paths), vias=tuple(vias))


def bias_copper(board: Board) -> RouteStage:
    """Resume bias routes from package ports, sharing nearby ground and filter paths."""
    fuse = board.electronic_fuse
    junction = fuse.port("overvoltage")
    top_pad = board.overvoltage_top.pin_position(ResistorPin.TERMINAL_A)
    midpoint = Point(
        (junction.x_mm + top_pad.x_mm) / 2, (junction.y_mm + top_pad.y_mm) / 2
    )
    bottom_pad = board.overvoltage_bottom.pin_position(ResistorPin.TERMINAL_A)
    bottom_escape = Point(bottom_pad.x_mm, bottom_pad.y_mm + 1.3)
    paths = (
        CopperPath(
            board.overvoltage_bottom.net(ResistorPin.TERMINAL_A),
            (board.overvoltage_bottom.endpoint(ResistorPin.TERMINAL_A), bottom_escape),
        ),
        CopperPath(
            board.enable_top.net(ResistorPin.TERMINAL_A),
            (
                board.enable_top.endpoint(ResistorPin.TERMINAL_A),
                board.switch_wetting_load.endpoint(ResistorPin.TERMINAL_A),
            ),
        ),
        CopperPath(
            board.overvoltage_bottom.net(ResistorPin.TERMINAL_A),
            (
                board.overvoltage_bottom.endpoint(ResistorPin.TERMINAL_A),
                board.overvoltage_filter.endpoint(CapacitorPin.TERMINAL_A),
            ),
        ),
    )
    nets = (
        NetRoute(
            fuse.net(EfusePin.ENABLE_UVLO),
            preferred_layer=BOTTOM,
            reserve_group=True,
            via_keepout_mm=1.2,
            escapes=((fuse.endpoint(EfusePin.ENABLE_UVLO), fuse.port("enable")),),
        ),
        NetRoute(
            fuse.net(EfusePin.OVERVOLTAGE_LOCKOUT),
            preferred_layer=BOTTOM,
            reserve_group=True,
            via_keepout_mm=1.2,
            omit=(
                fuse.endpoint(EfusePin.OVERVOLTAGE_LOCKOUT),
                fuse.endpoint(EfusePin.POWER_GOOD_THRESHOLD),
                board.overvoltage_filter.endpoint(CapacitorPin.TERMINAL_A),
            ),
            escapes=(
                (board.overvoltage_top.endpoint(ResistorPin.TERMINAL_A), midpoint),
                (
                    board.overvoltage_bottom.endpoint(ResistorPin.TERMINAL_A),
                    bottom_escape,
                ),
            ),
        ),
        NetRoute(
            board.power_connector.net(PowerHeaderPin.RUN),
            preferred_layer=BOTTOM,
            reserve_group=True,
            via_keepout_mm=1.2,
            last_reference=board.power_connector.reference,
            omit=(board.switch_wetting_load.endpoint(ResistorPin.TERMINAL_A),),
        ),
    )
    return RouteStage(
        paths=paths,
        vias=(
            Via(
                board.overvoltage_bottom.net(ResistorPin.TERMINAL_A),
                bottom_escape,
                0.9,
                0.4,
            ),
        ),
        nets=nets,
    )


def led_copper(board: Board) -> RouteStage:
    """Follow the actual LED chain; row links are straight, turns use side lanes."""
    paths: list[CopperPath] = [
        CopperPath(
            board.led_data_termination.net(ResistorPin.TERMINAL_B),
            (
                board.led_data_termination.endpoint(ResistorPin.TERMINAL_B),
                board.led_buffer.endpoint(Ahct125Pin.BUFFER_1_OUTPUT),
            ),
        )
    ]
    links: list[DirectLink] = []
    vias: list[Via[Net]] = []
    chain = tuple(board.leds.values())
    square_names = tuple(board.leds)
    for index, (source, receiver) in enumerate(pairwise(chain)):
        for output, input_pin in (
            (Sk9822Pin.DATA_OUT, Sk9822Pin.DATA_IN),
            (Sk9822Pin.CLOCK_OUT, Sk9822Pin.CLOCK_IN),
        ):
            driver_endpoint = source.endpoint(output)
            start = source.pin_position(output)
            net = source.net(output)
            if (
                output is Sk9822Pin.DATA_OUT
                and square_names[index] in board.led_turn_terminations
            ):
                termination = board.led_turn_terminations[square_names[index]]
                paths.append(
                    CopperPath(
                        net,
                        (driver_endpoint, termination.endpoint(ResistorPin.TERMINAL_B)),
                    )
                )
                driver_endpoint = termination.endpoint(ResistorPin.TERMINAL_A)
                start = termination.pin_position(ResistorPin.TERMINAL_A)
                net = termination.net(ResistorPin.TERMINAL_A)
            end = receiver.pin_position(input_pin)
            if source.placement.y_mm == receiver.placement.y_mm:
                links.append(
                    DirectLink(net, driver_endpoint, receiver.endpoint(input_pin))
                )
                continue
            right = start.x_mm > 0
            clock = output is Sk9822Pin.CLOCK_OUT
            reach = (3.0 if right else 7.0) if clock else (1.75 if right else 6.0)
            x = end.x_mm + (reach if right else -reach)
            first, second = Point(x, start.y_mm), Point(x, end.y_mm)
            paths.extend(
                (
                    CopperPath(net, (driver_endpoint, first)),
                    CopperPath(net, (second, receiver.endpoint(input_pin))),
                )
            )
            paths.append(
                CopperPath(
                    net,
                    (first, second),
                    layer=TOP if clock or right else CopperLayer.INNER_4,
                )
            )
            if not clock and not right:
                vias.extend(Via(net, point, 0.9, 0.4) for point in (first, second))
    return RouteStage(
        paths=tuple(paths),
        vias=tuple(vias),
        links=tuple(sorted(links, key=lambda link: link.net.label)),
    )


def routing_plan(board: Board) -> RoutingPlan:
    return RoutingPlan(
        root_reference=board.host_header.reference,
        power_nets=(
            BoardNet.GROUND,
            BoardNet.FIVE_VOLTS,
            BoardNet.THREE_VOLTS_THREE,
            BoardNet.LED_5V,
        ),
        power_exclusions=tuple(
            component.reference
            for component in (
                board.current_limit_resistor,
                board.slew_capacitor,
                board.timer_capacitor,
                board.overvoltage_filter,
            )
        ),
        stages=(
            power_copper(board),
            led_copper(board),
            RouteStage(nets=board.wiring),
            bias_copper(board),
        ),
    )
