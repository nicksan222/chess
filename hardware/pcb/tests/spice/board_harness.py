"""Readable board-aware circuit factory used only by electrical tests.

It translates validated board connections and component metadata into small
circuits. Tests own the actions and expectations; this module only removes SPICE
boilerplate and guarantees that test nodes correspond to the real PCB contract.
"""

from __future__ import annotations

import re
from fractions import Fraction

from base.design import BoardDesign
from components.ahct125 import Ahct125Pin
from components.electrical import (
    AHCT125,
    BOARD_POWER,
    HALL_SENSOR,
    LOGIC_3V3,
    PI_GPIO_PULLUP_OHMS,
)
from components.hall_sensor import HallSensorPin
from spice.circuit import SpiceCircuit
from spice.movement import MovementCase


def _node(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_").lower()


def _expect(name: str, occupied: bool) -> str:
    voltage = LOGIC_3V3.low if occupied else LOGIC_3V3.high
    return f"* EXPECT result_{name} {voltage.minimum} {voltage.maximum}"


class BoardHarness:
    """Build circuits whose topology comes from the real chess board."""

    def __init__(self, design: BoardDesign, led_brightness_max: Fraction) -> None:
        self.design = design
        self.led_brightness_max = led_brightness_max
        self.net_by_endpoint = {
            (str(reference), str(pin)): str(connection.name)
            for connection in design.connections.connections
            for reference, pin in connection.endpoints
        }
        self.square_nets = {
            str(name)[3:]: str(name)
            for (reference, pin), name in self.net_by_endpoint.items()
            if reference.startswith("HS") and pin == HallSensorPin.ACTIVE_LOW_OUTPUT
        }
        if len(self.square_nets) != 64:
            raise ValueError("SPICE generation requires all 64 Hall sensor nets")

    @staticmethod
    def _hall_model() -> list[str]:
        switch = (
            f"Ron={HALL_SENSOR.output_on_ohms} "
            f"Roff={HALL_SENSOR.output_off_spice} "
            f"Vt={HALL_SENSOR.magnetic_drive_threshold_volts} "
            f"Vh={HALL_SENSOR.magnetic_drive_hysteresis_volts}"
        )
        return [
            f".model HALLSW SW({switch})",
            ".subckt SQUARE_SENSOR OUT VDD MAG GND",
            "SOUTPUT OUT GND MAG GND HALLSW",
            f"RPULL OUT VDD {HALL_SENSOR.input_pullup_ohms}",
            ".ends SQUARE_SENSOR",
        ]

    def _component_count(self, part_key: str) -> int:
        return sum(
            component.spec.part_key == part_key
            for component in self.design.components.values()
        )

    def _component_value(self, part_key: str) -> str:
        values = [
            component.spec.value
            for component in self.design.components.values()
            if component.spec.part_key == part_key
        ]
        if len(values) != 1:
            raise ValueError(f"SPICE generation requires one {part_key}")
        return values[0]

    def _movement(self, scenario: MovementCase) -> str:
        if not scenario.checks:
            raise ValueError(f"{scenario.name}: movement case has no registered checks")
        touched = sorted(
            scenario.initially_occupied
            | {event.square for event in scenario.events}
            | {check.square for check in scenario.checks}
        )
        unknown = set(touched) - set(self.square_nets)
        if unknown:
            raise ValueError(f"unknown movement squares: {sorted(unknown)}")
        events_by_square = {square: [] for square in touched}
        for event in scenario.events:
            events_by_square[event.square].append(event)

        lines = [f"Generated chess-board {scenario.name} sensor sequence"]
        lines.extend(_expect(check.name, check.occupied) for check in scenario.checks)
        lines.extend(self._hall_model())
        lines.append(f"VDD vdd 0 {LOGIC_3V3.supply_volts}")
        for square in touched:
            points = [(0.0, square in scenario.initially_occupied)]
            for event in events_by_square[square]:
                points.extend(
                    (
                        (event.at_ms - 0.001, points[-1][1]),
                        (event.at_ms, event.occupied),
                    )
                )
            waveform = " ".join(
                f"{at}m {LOGIC_3V3.supply_volts if occupied else 0}"
                for at, occupied in points
            )
            node = _node(self.square_nets[square])
            lines.extend(
                (
                    f"VMAG_{node} mag_{node} 0 PWL({waveform})",
                    f"X{node} {node} vdd mag_{node} 0 SQUARE_SENSOR",
                )
            )
        stop = (
            max(
                *(event.at_ms for event in scenario.events),
                *(check.at_ms for check in scenario.checks),
            )
            + 1
        )
        lines.append(f".tran 10u {stop}m")
        lines.extend(
            f".meas tran result_{check.name} "
            f"FIND v({_node(self.square_nets[check.square])}) AT={check.at_ms}m"
            for check in scenario.checks
        )
        lines.append(".end")
        return "\n".join(lines) + "\n"

    def _all_squares(self) -> str:
        lines = ["Generated chess-board exhaustive Hall sensor matrix"]
        for square in sorted(self.square_nets):
            lines.append(_expect(_node(square), True))
        lines.extend(self._hall_model())
        lines.extend(
            (
                f"VDD vdd 0 {LOGIC_3V3.supply_volts}",
                f"VMAG mag 0 {LOGIC_3V3.supply_volts}",
            )
        )
        for square, net in sorted(self.square_nets.items()):
            lines.append(f"X{_node(square)} {_node(net)} vdd mag 0 SQUARE_SENSOR")
        lines.append(".tran 1u 10u")
        for square, net in sorted(self.square_nets.items()):
            lines.append(
                f".meas tran result_{_node(square)} FIND v({_node(net)}) AT=5u"
            )
        lines.append(".end")
        return "\n".join(lines) + "\n"

    def _level_shifter(self) -> str:
        channels = (
            (
                Ahct125Pin.BUFFER_1_INPUT,
                Ahct125Pin.BUFFER_1_OUTPUT,
                False,
            ),
            (
                Ahct125Pin.BUFFER_2_INPUT,
                Ahct125Pin.BUFFER_2_OUTPUT,
                True,
            ),
        )
        lines = [
            "Generated chess-board AHCT125 level-shifter channels",
            f"* EXPECT result_channel_1 {AHCT125.low.minimum} {AHCT125.low.maximum}",
            f"* EXPECT result_channel_2 {AHCT125.high.minimum} {AHCT125.high.maximum}",
            f"V5 rail_5v 0 {AHCT125.supply_volts}",
        ]
        for index, (input_pin, output_pin, high) in enumerate(channels, start=1):
            input_net = self.net_by_endpoint[("U5", str(input_pin))]
            output_net = self.net_by_endpoint[("U5", str(output_pin))]
            input_node = _node(input_net)
            output_node = _node(output_net)
            output_expression = (
                f"BOUT{index} {output_node} 0 "
                f"V={{V({input_node})>{AHCT125.input_high_threshold_volts} ? "
                f"V(rail_5v)-{AHCT125.output_headroom_volts} : "
                f"{AHCT125.output_headroom_volts}}}"
            )
            lines.extend(
                (
                    f"VIN{index} {input_node} 0 {LOGIC_3V3.supply_volts if high else 0}",
                    output_expression,
                )
            )
        output_1 = _node(self.net_by_endpoint[("U5", str(Ahct125Pin.BUFFER_1_OUTPUT))])
        output_2 = _node(self.net_by_endpoint[("U5", str(Ahct125Pin.BUFFER_2_OUTPUT))])
        lines.extend(
            (
                ".tran 1u 10u",
                f".meas tran result_channel_1 FIND v({output_1}) AT=5u",
                f".meas tran result_channel_2 FIND v({output_2}) AT=5u",
                ".end",
            )
        )
        return "\n".join(lines) + "\n"

    def _open_drain_inputs(self) -> str:
        bus_nets = ("I2C_SDA", "I2C_SCL", "SENSE_IRQ")
        lines = ["Generated chess-board open-drain bus inputs"]
        for name in bus_nets:
            lines.extend(
                (
                    _expect(f"{_node(name)}_released", False),
                    _expect(f"{_node(name)}_low", True),
                )
            )
        lines.extend(
            (
                (
                    f".model INPUTSW SW(Ron={HALL_SENSOR.output_on_ohms} "
                    f"Roff={HALL_SENSOR.output_off_spice} "
                    f"Vt={HALL_SENSOR.magnetic_drive_threshold_volts} "
                    f"Vh={HALL_SENSOR.magnetic_drive_hysteresis_volts})"
                ),
                f"VDD vdd 0 {LOGIC_3V3.supply_volts}",
                f"VDRIVE drive 0 PULSE(0 {LOGIC_3V3.supply_volts} 1m 1u 1u 10 20)",
            )
        )
        for index, name in enumerate(bus_nets, start=1):
            resistor = next(
                component
                for component in self.design.components.values()
                if component.spec.part_key == "RES_4K7"
                and name
                in {
                    self.net_by_endpoint.get((component.reference, "1")),
                    self.net_by_endpoint.get((component.reference, "2")),
                }
            )
            node = _node(name)
            lines.extend(
                (
                    f"RPULL{index} {node} vdd {resistor.spec.value}",
                    f"SDRIVE{index} {node} 0 drive 0 INPUTSW",
                )
            )
        lines.append(".tran 10u 3m")
        for name in bus_nets:
            node = _node(name)
            lines.extend(
                (
                    f".meas tran result_{node}_released FIND v({node}) AT=0.5m",
                    f".meas tran result_{node}_low FIND v({node}) AT=1.5m",
                )
            )
        lines.append(".end")
        return "\n".join(lines) + "\n"

    def _buttons(self) -> str:
        button_nets = sorted(
            str(connection.name)
            for connection in self.design.connections.connections
            if connection.name and str(connection.name).startswith("BTN_")
        )
        lines = ["Generated chess-board complete button input bank"]
        lines.extend(_expect(_node(name), True) for name in button_nets)
        lines.extend((f"VDD vdd 0 {LOGIC_3V3.supply_volts}", "VGROUND pressed 0 0"))
        for index, name in enumerate(button_nets, start=1):
            node = _node(name)
            lines.extend(
                (
                    f"RPULL{index} {node} vdd {PI_GPIO_PULLUP_OHMS}",
                    f"RSWITCH{index} {node} pressed {HALL_SENSOR.output_on_ohms}",
                )
            )
        lines.append(".tran 1u 10u")
        lines.extend(
            f".meas tran result_{_node(name)} FIND v({_node(name)}) AT=5u"
            for name in button_nets
        )
        lines.append(".end")
        return "\n".join(lines) + "\n"

    def _power_startup(self) -> str:
        capacitors = []
        for component in self.design.components.values():
            if not component.spec.part_key.startswith("CAP_"):
                continue
            if self.net_by_endpoint.get((component.reference, "1")) != "+5V":
                continue
            value = (
                component.spec.value.split()[0].replace("uF", "u").replace("nF", "n")
            )
            capacitors.append((component.reference, value))
        lines = [
            "Generated chess-board fitted-capacitor startup",
            (
                f"* EXPECT result_5v_at_1ms {BOARD_POWER.healthy_rail.minimum} "
                f"{BOARD_POWER.healthy_rail.maximum}"
            ),
            f"VINPUT source 0 PULSE(0 {BOARD_POWER.supply_volts} 0 1u 1u 10 20)",
            f"RPATH source rail_5v {BOARD_POWER.path_ohms}",
            (
                f"BLOAD rail_5v 0 I={BOARD_POWER.host_and_logic_amps}*"
                f"tanh(V(rail_5v)/{BOARD_POWER.load_soft_start_volts})"
            ),
        ]
        lines.extend(
            f"C{reference} rail_5v 0 {value}" for reference, value in capacitors
        )
        lines.extend(
            (".tran 5u 2m", ".meas tran result_5v_at_1ms FIND v(rail_5v) AT=1m", ".end")
        )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _power_off() -> str:
        return "\n".join(
            (
                "Generated chess-board open power switch",
                (
                    f"* EXPECT result_5v {BOARD_POWER.off_rail.minimum} "
                    f"{BOARD_POWER.off_rail.maximum}"
                ),
                f"VINPUT source 0 {BOARD_POWER.supply_volts}",
                "RSWITCH source rail_5v 1T",
                "RBLEED rail_5v 0 10k",
                ".tran 1u 10u",
                ".meas tran result_5v FIND v(rail_5v) AT=5u",
                ".end",
                "",
            )
        )

    def power_current(self, *, full_white: bool = False) -> float:
        led_count = self._component_count("SK9822")
        brightness = Fraction(1) if full_white else self.led_brightness_max
        return BOARD_POWER.host_and_logic_amps + (
            led_count * BOARD_POWER.led_full_white_amps_each * float(brightness)
        )

    def _power(self, full_white: bool) -> str:
        load = self.power_current(full_white=full_white)
        fuse_rating = float(self._component_value("FUSE_2A").split()[0])
        overloaded = load > fuse_rating
        name = "full-white" if full_white else "approved"
        lines = [
            f"Generated chess-board {name} power load",
            (
                f"* EXPECT result_current "
                f"{load - BOARD_POWER.current_tolerance_amps} "
                f"{load + BOARD_POWER.current_tolerance_amps}"
            ),
            (
                f"* EXPECT result_5v {BOARD_POWER.overloaded_rail.minimum} "
                f"{BOARD_POWER.overloaded_rail.maximum}"
                if overloaded
                else f"* EXPECT result_5v {BOARD_POWER.healthy_rail.minimum} "
                f"{BOARD_POWER.healthy_rail.maximum}"
            ),
            f"VINPUT source 0 {BOARD_POWER.supply_volts}",
            f"RPATH source rail_5v {BOARD_POWER.path_ohms}",
            f"ILOAD rail_5v 0 {load}",
            ".tran 1u 10u",
            ".meas tran result_5v FIND v(rail_5v) AT=5u",
            ".meas tran input_current FIND i(VINPUT) AT=5u",
            ".meas tran result_current PARAM='-input_current'",
            ".end",
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _circuit(source: str) -> SpiceCircuit:
        title, *rows = source.rstrip().splitlines()
        circuit = SpiceCircuit(title)
        for row in rows:
            if row == ".end":
                continue
            if row.startswith("* EXPECT result_"):
                _comment, _expect, name, minimum, maximum = row.split()
                circuit.expect(
                    name.removeprefix("result_"), float(minimum), float(maximum)
                )
            elif row.startswith(".meas ") and " PARAM=" in row:
                prefix, expression = row.removeprefix(".meas tran ").split(" PARAM=")
                circuit.control(f"let {prefix}={expression.strip(chr(39))}")
                circuit.control(f"print {prefix}")
            elif row.startswith(".meas "):
                circuit.control(row.removeprefix("."))
            else:
                circuit.raw(row)
        return circuit

    def movement(self, case: MovementCase) -> SpiceCircuit:
        return self._circuit(self._movement(case))

    def all_squares(self) -> SpiceCircuit:
        return self._circuit(self._all_squares())

    def level_shifter(self) -> SpiceCircuit:
        return self._circuit(self._level_shifter())

    def open_drain_inputs(self) -> SpiceCircuit:
        return self._circuit(self._open_drain_inputs())

    def buttons(self) -> SpiceCircuit:
        return self._circuit(self._buttons())

    def power(self, *, full_white: bool = False) -> SpiceCircuit:
        return self._circuit(self._power(full_white))

    def power_off(self) -> SpiceCircuit:
        return self._circuit(self._power_off())

    def power_startup(self) -> SpiceCircuit:
        return self._circuit(self._power_startup())
