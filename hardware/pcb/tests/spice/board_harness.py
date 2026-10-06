"""Readable board-aware circuit factory used only by electrical tests.

It translates validated board connections and component metadata into small
circuits. Tests own the actions and expectations; this module only removes SPICE
boilerplate and guarantees that test nodes correspond to the real PCB contract.
"""

from __future__ import annotations

import math
import re
from fractions import Fraction
from itertools import combinations

import pcbnew

from pcb.definition.native import connections, parts
from pcb.definition.parts.fuse import INPUT_FUSE
from pcb.definition.parts.power_header import POWER_ENTRY_HEADER
from shared import wiring
from shared.electronics import (
    Ahct125Pin,
    BarrelJackPin,
    ComponentReference,
    EfusePin,
    FusePin,
    HallSensorPin,
    PowerSwitchPin,
    RaspberryPiHeaderPin,
    ResistorPin,
    Sk9822Pin,
    Tca9554Pin,
    TestPointPin,
)
from shared.electronics.harness import POWER_HARNESS
from shared.panel_buttons import PANEL_BUTTONS
from spice import datasheets
from spice.circuit import SpiceCircuit
from spice.electrical import CONTROL_SWITCH, LOGIC_3V3
from spice.movement import MovementCase, SensorEvent

BUTTON_WINDOW_MS = 1.0


def _node(name: str) -> str:
    """A SPICE-safe lowercase node name from a net name (non-alphanumerics become underscores)."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_").lower()


def _expect(name: str, occupied: bool) -> str:
    """An `* EXPECT` marker comment that `_circuit` later turns into a real assertion: a Hall
    output must be in the logic-low window when occupied and the logic-high window when empty.
    """
    voltage = LOGIC_3V3.low if occupied else LOGIC_3V3.high
    return f"* EXPECT result_{name} {voltage.minimum} {voltage.maximum}"


class BoardHarness:
    """Build circuits whose topology comes from the real chess board."""

    def __init__(self, design: pcbnew.BOARD, led_brightness_max: Fraction) -> None:
        self.design = design
        self.components = {f.GetReference(): f for f in parts(design)}
        self.connections = connections(design)
        self.led_brightness_max = led_brightness_max
        self.net_by_endpoint = {
            (str(reference), str(pin)): str(name)
            for name, endpoints in self.connections.items()
            for reference, pin in endpoints
        }
        self.endpoints_by_net = {
            str(name): {(str(reference), str(pin)) for reference, pin in endpoints}
            for name, endpoints in self.connections.items()
        }
        self.square_nets = self._validated_square_nets()

    def _required_endpoints(
        self,
        net: str,
        expected: set[tuple[str, str]],
    ) -> None:
        """Require that `net` connects exactly `expected` (reference, pin) endpoints, else raise."""
        actual = self.endpoints_by_net.get(net)
        if actual != expected:
            raise ValueError(
                f"{net} must connect {sorted(expected)}; found {sorted(actual or set())}"
            )

    def _validated_square_nets(self) -> dict[str, str]:
        """Map each square to its sense net after checking the sensor, expander pin and net all agree with the shared mapping."""
        found: dict[str, str] = {}
        for reference, component in self.components.items():
            if component.GetFieldText("PartKey") != "HALL_SENSOR":
                continue
            square = component.GetFieldText("Square")
            position = wiring.parse_square(square)
            assignment = wiring.expander_of(position)
            expander_pin = Tca9554Pin[f"P{assignment.pin_index}"]
            bank_label = assignment.bank.label
            expander_reference = next(
                candidate_reference
                for candidate_reference, candidate in self.components.items()
                if candidate.GetFieldText("PartKey") == "TCA9554"
                and candidate.GetFieldText("Bank") == bank_label
            )
            self._required_net(reference, HallSensorPin.SUPPLY, "+3V3")
            self._required_net(reference, HallSensorPin.GROUND, "GND")
            net = wiring.sense_net(square)
            self._required_endpoints(
                net,
                {
                    (reference, str(HallSensorPin.ACTIVE_LOW_OUTPUT)),
                    (expander_reference, str(expander_pin)),
                },
            )
            found[square] = net
        if len(found) != 64:
            raise ValueError("SPICE generation requires all 64 Hall sensor nets")
        return found

    @staticmethod
    def _hall_model() -> list[str]:
        """SPICE rows for the Hall output switch, with on-resistance from the DRV5032's guaranteed VOL at 1 mA."""
        switch = (
            f"Ron={datasheets.DRV5032_VOL_AT_1MA / 1e-3} "
            f"Roff={CONTROL_SWITCH.off_spice} "
            f"Vt={CONTROL_SWITCH.drive_threshold_volts} "
            f"Vh={CONTROL_SWITCH.drive_hysteresis_volts}"
        )
        return [
            f".model HALLSW SW({switch})",
            ".subckt SQUARE_SENSOR OUT VDD MAG GND",
            "SOUTPUT OUT GND MAG GND HALLSW",
            f"RPULL OUT VDD {datasheets.TCA9554_PULLUP_OHMS_TYPICAL}",
            ".ends SQUARE_SENSOR",
        ]

    def _required_net(self, reference: str, pin: str, expected: str) -> str:
        """Require pin `pin` of `reference` to be on net `expected`, else raise (so the circuit cannot be built from a mis-wired board)."""
        actual = self.net_by_endpoint.get((reference, pin))
        if actual is None or actual != expected:
            raise ValueError(
                f"{reference} pin {pin} must be on {expected} for simulation; "
                f"found {actual}"
            )
        return actual

    def power_topology(self) -> dict[str, str]:
        """Check the S4b supply chain on the board and name each part by role.

        Plug tip -> J4 (harness definition) -> F1 -> DC_FUSED -> U74 IN, U74 OUT on
        +5V; the rocker's cavities feed RUN from DC_FUSED. Dividers and bias parts
        are found by the nets they join, not by reference.
        """
        cavity = {
            (wire.far_part, wire.far_terminal): wire.cavity for wire in POWER_HARNESS
        }
        header = POWER_ENTRY_HEADER.reference
        tip = cavity[("BARREL_JACK", BarrelJackPin.CENTRE_POSITIVE)]
        if (
            self._pad_node(header, cavity[("BARREL_JACK", BarrelJackPin.SLEEVE_GROUND)])
            != "0"
        ):
            raise ValueError("the plug sleeve must reach board ground through J4")
        if self._pad_node(
            INPUT_FUSE.reference, FusePin.UNFUSED_INPUT
        ) != self._pad_node(header, tip):
            raise ValueError("the fuse must follow the plug tip")
        fused = self.net_by_endpoint[(INPUT_FUSE.reference, str(FusePin.FUSED_OUTPUT))]
        efuse = ComponentReference.INPUT_EFUSE
        self._required_net(efuse, EfusePin.INPUT, fused)
        self._required_net(efuse, EfusePin.OUTPUT, "+5V")
        to_rocker = cavity[("POWER_SWITCH", PowerSwitchPin.FUSED_INPUT)]
        from_rocker = cavity[("POWER_SWITCH", PowerSwitchPin.RUN_OUTPUT)]
        self._required_net(header, to_rocker, fused)
        run = self.net_by_endpoint[(header, from_rocker)]
        enable = self.net_by_endpoint[(efuse, str(EfusePin.ENABLE_UVLO))]
        ovlo = self.net_by_endpoint[(efuse, str(EfusePin.OVERVOLTAGE_LOCKOUT))]
        roles = {"fused": fused, "run": run, "enable": enable, "ovlo": ovlo}
        found: dict[str, str] = {}
        for reference, component in self.components.items():
            if not component.GetFieldText("PartKey").startswith("RES_"):
                continue
            nets = frozenset(
                self.net_by_endpoint.get((reference, pin), "") for pin in ("1", "2")
            )
            for role, pair in (
                ("ovlo_top", {fused, ovlo}),
                ("ovlo_bottom", {ovlo, "GND"}),
                ("enable_top", {run, enable}),
                ("enable_bottom", {enable, "GND"}),
                ("wetting", {run, "GND"}),
                (
                    "limit",
                    {self.net_by_endpoint[(efuse, str(EfusePin.CURRENT_LIMIT))], "GND"},
                ),
            ):
                if nets == frozenset(pair):
                    found[role] = reference
        if len(found) != 6:
            raise ValueError(f"eFuse bias network incomplete: {sorted(found)}")
        return roles | found

    def resistor_ohms(self, reference: str) -> tuple[float, float]:
        """Nominal ohms and tolerance of a placed resistor (value field, MPN series)."""
        component = self.components[reference]
        value = component.GetFieldText("NominalValue").split()[0]
        ohms = float(value.rstrip("kR")) * (1000.0 if value.endswith("k") else 1.0)
        series = component.GetValue()[:2]
        return ohms, datasheets.RESISTOR_TOLERANCE[series]

    def _component_count(self, part_key: str) -> int:
        """How many placed footprints have `part_key`."""
        return sum(
            component.GetFieldText("PartKey") == part_key
            for component in self.components.values()
        )

    def _component_value(self, part_key: str) -> str:
        """The nominal value of the single footprint with `part_key`; raises unless there is exactly one."""
        values = [
            component.GetFieldText("NominalValue")
            for component in self.components.values()
            if component.GetFieldText("PartKey") == part_key
        ]
        if len(values) != 1:
            raise ValueError(f"SPICE generation requires one {part_key}")
        return values[0]

    def _movement(self, scenario: MovementCase) -> str:
        """Circuit text for a movement case: the touched squares' sensors, their expander inputs, timed events and checks."""
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
        events_by_square: dict[str, list[SensorEvent]] = {
            square: [] for square in touched
        }
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

    def hall_levels(self, *, occupied: bool, vcc: float) -> SpiceCircuit:
        """Every square's DRV5032 open drain against its TCA9554 pull-up (DC).

        Occupied: the output sinks through its worst on-resistance (VOL 0.3 V at
        1 mA) against the strongest pull-up the TCA9554's IIL limit allows. Empty:
        the off output's leakage plus the expander's input leakage load the typical
        pull-up (no maximum is stated). result_<square> is the margin in volts to
        the TCA9554 VIL (occupied) or VIH (empty) at this VCC.
        """
        state = "occupied" if occupied else "empty"
        circuit = SpiceCircuit(f"Generated chess-board Hall levels, {state}, {vcc:g} V")
        circuit.rows.append(f"VDD vdd 0 {vcc}")
        on_ohms = datasheets.DRV5032_VOL_AT_1MA / 1e-3
        strongest = vcc / datasheets.TCA9554_PULLUP_AMPS_MAX
        leakage = (
            datasheets.DRV5032_LEAKAGE_AMPS + datasheets.TCA9554_INPUT_LEAKAGE_AMPS
        )
        for square, net in sorted(self.square_nets.items()):
            node = _node(net)
            if occupied:
                circuit.rows.extend(
                    (
                        f"RPU_{node} {node} vdd {strongest}",
                        f"RON_{node} {node} 0 {on_ohms}",
                    )
                )
                margin = f"{datasheets.TCA9554_VIL_FRACTION * vcc} - v({node})"
            else:
                circuit.rows.extend(
                    (
                        f"RPU_{node} {node} vdd {datasheets.TCA9554_PULLUP_OHMS_TYPICAL}",
                        f"ILEAK_{node} {node} 0 {leakage}",
                    )
                )
                margin = f"v({node}) - {datasheets.TCA9554_VIH_FRACTION * vcc}"
            circuit.controls.append(f"let result_{_node(square)} = {margin}")
            circuit.expect(_node(square), 0.0, vcc)
        circuit.rows.append(".op")
        return circuit

    def level_shifter(self, *, vcc: float, high: bool) -> SpiceCircuit:
        """Pi GPIO -> AHCT125 -> first SK9822, as datasheet Thevenin sources (DC).

        The Pi output is its guaranteed VOH/VOL at 2 mA (the real load is microamps).
        The AHCT125 output is the line through its two datasheet VOH (VOL) points at
        VCC 4.5 V, moved with VCC. result_<channel>_input is the margin to the AHCT
        VIH/VIL; result_<channel>_led the margin to SK9822 0.7/0.3 x VDD (LED_5V
        switched on from +5V, so VDD = VCC). The enable pins must be on LED_OE_N,
        which U75 holds low only once the LED rail is up (S6b).
        """
        self._required_net("U5", Ahct125Pin.SUPPLY, "+5V")
        self._required_net("U5", Ahct125Pin.GROUND, "GND")
        # S6: the LEDs run from the switched LED_5V; these DC cases are the enabled
        # state (Q1 on, LED_5V = +5V less milliohms; U5 enabled by LED_EN_N low).
        self._required_net("U6", Sk9822Pin.FIVE_VOLTS, wiring.LED_SUPPLY_NET)
        (i_small, v_small), (i_large, v_large) = (
            datasheets.AHCT125_VOH_POINTS if high else datasheets.AHCT125_VOL_POINTS
        )
        ohms = abs(v_small - v_large) / (i_large - i_small)
        shift = vcc - datasheets.AHCT125_VOH_TEST_VCC if high else 0.0
        open_volts = (
            v_small + i_small * ohms if high else v_small - i_small * ohms
        ) + shift
        level = "high" if high else "low"
        circuit = SpiceCircuit(
            f"Generated chess-board LED level shift, {level}, {vcc:g} V"
        )
        channels = (
            (
                Ahct125Pin.BUFFER_1_OUTPUT_ENABLE,
                Ahct125Pin.BUFFER_1_INPUT,
                Ahct125Pin.BUFFER_1_OUTPUT,
                RaspberryPiHeaderPin.SPI_DATA_GPIO10,
                "TP3",
                Sk9822Pin.DATA_IN,
            ),
            (
                Ahct125Pin.BUFFER_2_OUTPUT_ENABLE,
                Ahct125Pin.BUFFER_2_INPUT,
                Ahct125Pin.BUFFER_2_OUTPUT,
                RaspberryPiHeaderPin.SPI_CLOCK_GPIO11,
                "TP4",
                Sk9822Pin.CLOCK_IN,
            ),
        )
        for (
            enable_pin,
            input_pin,
            output_pin,
            host_pin,
            test_point,
            led_pin,
        ) in channels:
            self._required_net("U5", enable_pin, wiring.LED_OUTPUT_ENABLE_N_NET)
            input_net = self.net_by_endpoint[("U5", str(input_pin))]
            output_net = self.net_by_endpoint[("U5", str(output_pin))]
            self._required_endpoints(
                input_net, {("J1", str(host_pin)), ("U5", str(input_pin))}
            )
            # S5: the data channel reaches the LED through R9 (source termination).
            series = ComponentReference.LED_DATA_TERMINATION
            driven = ("U5", str(output_pin))
            led_net, series_rows = output_net, []
            if (series, str(ResistorPin.TERMINAL_B)) in self.endpoints_by_net[
                output_net
            ]:
                self._required_endpoints(
                    output_net, {driven, (series, str(ResistorPin.TERMINAL_B))}
                )
                led_net = self.net_by_endpoint[(series, str(ResistorPin.TERMINAL_A))]
                driven = (series, str(ResistorPin.TERMINAL_A))
                ohms_series = self.resistor_ohms(series)[0]
                series_rows = [
                    f"RSER_{_node(output_net)} {_node(output_net)} {_node(led_net)} {ohms_series}"
                ]
            # S6d: a 10 kOhm pull-down holds the LED input low while U5 is Hi-Z;
            # it loads the driver here.
            pull_downs = self.pull_downs(led_net)
            self._required_endpoints(
                led_net,
                {
                    driven,
                    ("U6", str(led_pin)),
                    (test_point, str(TestPointPin.PROBE)),
                    *((reference, pin) for reference, pin, _ in pull_downs),
                },
            )
            circuit.rows.extend(series_rows)
            circuit.rows.extend(
                f"RPD_{reference} {_node(led_net)} 0 {ohms}"
                for reference, _, ohms in pull_downs
            )
            name, node_in, node_out = (
                _node(led_net),
                _node(input_net),
                _node(led_net),
            )
            buffer_node = _node(output_net)
            host = (
                datasheets.PI_GPIO_VOH_AT_2MA if high else datasheets.PI_GPIO_VOL_AT_2MA
            )
            circuit.rows.extend(
                (
                    f"VHOST_{name} {node_in} 0 {host}",
                    f"VBUF_{name} open_{name} 0 {open_volts}",
                    f"RBUF_{name} open_{name} {buffer_node} {ohms}",
                )
            )
            if high:
                circuit.controls.extend(
                    (
                        f"let result_{name}_input = v({node_in}) - {datasheets.AHCT125_VIH}",
                        (
                            f"let result_{name}_led = v({node_out}) - "
                            f"{datasheets.SK9822_VIH_FRACTION * vcc}"
                        ),
                    )
                )
            else:
                circuit.controls.extend(
                    (
                        f"let result_{name}_input = {datasheets.AHCT125_VIL} - v({node_in})",
                        (
                            f"let result_{name}_led = "
                            f"{datasheets.SK9822_VIL_FRACTION * vcc} - v({node_out})"
                        ),
                    )
                )
            circuit.expect(f"{name}_input", 0.0, vcc)
            circuit.expect(f"{name}_led", 0.0, vcc)
        circuit.rows.append(".op")
        return circuit

    def pull_downs(self, net: str) -> list[tuple[str, str, float]]:
        """Resistors from `net` to GND: (reference, pin on `net`, nominal ohms)."""
        found: list[tuple[str, str, float]] = []
        for reference, pin in sorted(self.endpoints_by_net.get(net, ())):
            if (
                not self.components[reference]
                .GetFieldText("PartKey")
                .startswith("RES_")
            ):
                continue
            other = "2" if pin == "1" else "1"
            if self.net_by_endpoint.get((reference, other)) == "GND":
                found.append((reference, pin, self.resistor_ohms(reference)[0]))
        return found

    def _open_drain_inputs(self) -> str:
        """Circuit text for the open-drain buses and Hall inputs: pull-ups and device pins taken from the board."""
        bus_nets = (wiring.SDA_NET, wiring.SCL_NET)
        expander_references = tuple(
            reference
            for reference, component in self.components.items()
            if component.GetFieldText("PartKey") == "TCA9554"
        )
        bus_endpoints = {
            wiring.SDA_NET: {
                ("J1", str(RaspberryPiHeaderPin.I2C_SDA)),
                ("J2", "4"),
                ("TP7", str(TestPointPin.PROBE)),
                *(
                    (reference, str(Tca9554Pin.I2C_DATA))
                    for reference in expander_references
                ),
            },
            wiring.SCL_NET: {
                ("J1", str(RaspberryPiHeaderPin.I2C_SCL)),
                ("J2", "3"),
                ("TP6", str(TestPointPin.PROBE)),
                *(
                    (reference, str(Tca9554Pin.I2C_CLOCK))
                    for reference in expander_references
                ),
            },
        }
        for net, endpoints in bus_endpoints.items():
            self._required_endpoints(net, endpoints)
        lines = ["Generated chess-board open-drain bus inputs"]
        for name in bus_nets:
            lines.extend(
                (
                    _expect(f"{_node(name)}_released", False),
                    _expect(f"{_node(name)}_low", True),
                )
            )
        supply_node = _node("+3V3")
        lines.extend(
            (
                (
                    f".model INPUTSW SW(Ron={CONTROL_SWITCH.on_ohms} "
                    f"Roff={CONTROL_SWITCH.off_spice} "
                    f"Vt={CONTROL_SWITCH.drive_threshold_volts} "
                    f"Vh={CONTROL_SWITCH.drive_hysteresis_volts})"
                ),
                f"VDD {supply_node} 0 {LOGIC_3V3.supply_volts}",
                f"VDRIVE drive 0 PULSE(0 {LOGIC_3V3.supply_volts} 1m 1u 1u 10 20)",
            )
        )
        # The only pull-ups are the Pi's own (Zero 2 W R23/R24, GPIO2/GPIO3 to 3V3);
        # the board must not add any (S5: R1/R2 removed).
        for name in bus_nets:
            extra = sorted(
                reference
                for reference, _pin in self.endpoints_by_net[name]
                if self.components[reference].GetFieldText("PartKey").startswith("RES_")
            )
            if extra:
                raise ValueError(f"{name}: unexpected on-board pull-up {extra}")
        pullup = datasheets.PI_I2C_PULLUP_OHMS * (
            1 + datasheets.PI_I2C_PULLUP_TOLERANCE
        )
        for index, name in enumerate(bus_nets, start=1):
            node = _node(name)
            lines.extend(
                (
                    f"RPULL{index} {node} {supply_node} {pullup}",
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

    def _pad_node(self, reference: str, pad_number: str) -> str:
        """SPICE node of one physical pad's actual net (board ground is node 0)."""
        component = self.components[reference]
        pad = next(p for p in component.Pads() if p.GetNumber() == pad_number)
        name = str(pad.GetNetname())
        return "0" if name == "GND" else _node(name)

    def _tactile_switch(self, reference: str, control: str) -> list[str]:
        """TL1105 internals from its lead geometry (datasheet p25), not pad names."""
        pads = list(self.components[reference].Pads())
        lines: list[str] = []
        for first, second in combinations(pads, 2):
            gap = pcbnew.ToMM(
                round(
                    math.hypot(
                        first.GetPosition().x - second.GetPosition().x,
                        first.GetPosition().y - second.GetPosition().y,
                    )
                )
            )
            a = self._pad_node(reference, first.GetNumber())
            b = self._pad_node(reference, second.GetNumber())
            tag = f"{reference}_{first.GetNumber()}_{second.GetNumber()}"
            tolerance = datasheets.TL1105_LEAD_PITCH_TOLERANCE_MM
            if abs(gap - datasheets.TL1105_STRAPPED_LEAD_PITCH_MM) <= tolerance:
                lines.append(f"RSTRAP_{tag} {a} {b} {datasheets.TL1105_STRAP_OHMS}")
            elif abs(gap - datasheets.TL1105_BRIDGED_LEAD_PITCH_MM) <= tolerance:
                lines.append(f"SDOME_{tag} {a} {b} {control} 0 TL1105_DOME")
        if sum(line.startswith("RSTRAP_") for line in lines) != 2 or (
            sum(line.startswith("SDOME_") for line in lines) != 2
        ):
            raise ValueError(f"{reference}: pads do not match the TL1105 lead pattern")
        return lines

    def _buttons(self) -> str:
        """Press each panel button alone; every other GPIO must stay released."""
        switches = sorted(
            reference
            for reference, component in self.components.items()
            if component.GetFieldText("PartKey") == "BUTTON"
        )
        lines.append(".end")
        return "\n".join(lines) + "\n"

    def _power_startup(self) -> str:
        dc_input, dc_fused, five_volts = self._power_path_nets()
        input_node = _node(dc_input)
        fused_node = _node(dc_fused)
        rail_node = _node(five_volts)
        capacitors: list[tuple[str, str]] = []
        five_volt_capacitor_roles = {
            "LED rail bulk capacitor",
            "Rail decoupling capacitor",
            "Buffer decoupling capacitor",
            "Local LED decoupling capacitor",
        }
        for component in self.components.values():
            if component.GetFieldText("Purpose") not in five_volt_capacitor_roles:
                continue
            self._required_net(
                component.GetReference(),
                CapacitorPin.SUPPLY_OR_ELECTRODE_A,
                "+5V",
            )
            self._required_net(
                component.GetReference(),
                CapacitorPin.RETURN_OR_ELECTRODE_B,
                "GND",
            )
            value = (
                component.GetFieldText("NominalValue")
                .split()[0]
                .replace("uF", "u")
                .replace("nF", "n")
            )
            capacitors.append((component.GetReference(), value))
        lines = [
            "Generated chess-board fitted-capacitor startup",
            (
                f"* EXPECT result_5v_at_1ms {BOARD_POWER.healthy_rail.minimum} "
                f"{BOARD_POWER.healthy_rail.maximum}"
            ),
            f"VINPUT {input_node} 0 PULSE(0 {BOARD_POWER.supply_volts} 0 1u 1u 10 20)",
            f"RFUSE {input_node} {fused_node} {BOARD_POWER.path_ohms / 2}",
            f"RSWITCH {fused_node} {rail_node} {BOARD_POWER.path_ohms / 2}",
            (
                f"BLOAD {rail_node} 0 I={BOARD_POWER.host_and_logic_amps}*"
                f"tanh(V({rail_node})/{BOARD_POWER.load_soft_start_volts})"
            ),
        ]
        lines.extend(
            f"C{reference} {rail_node} 0 {value}" for reference, value in capacitors
        )
        lines.extend(
            (
                ".tran 5u 2m",
                f".meas tran result_5v_at_1ms FIND v({rail_node}) AT=1m",
                ".end",
            )
        )
        return "\n".join(lines) + "\n"

    def _power_off(self) -> str:
        dc_input, dc_fused, five_volts = self._power_path_nets()
        input_node = _node(dc_input)
        fused_node = _node(dc_fused)
        rail_node = _node(five_volts)
        return "\n".join(
            (
                "Generated chess-board open power switch",
                (
                    f"* EXPECT result_5v {BOARD_POWER.off_rail.minimum} "
                    f"{BOARD_POWER.off_rail.maximum}"
                ),
                f"VINPUT {input_node} 0 {BOARD_POWER.supply_volts}",
                f"RFUSE {input_node} {fused_node} {BOARD_POWER.path_ohms}",
                f"RSWITCH {fused_node} {rail_node} 1T",
                f"RBLEED {rail_node} 0 10k",
                ".tran 1u 10u",
                f".meas tran result_5v FIND v({rail_node}) AT=5u",
                ".end",
                "",
            )
        )

    def power_current(self, *, full_white: bool = False) -> float:
        leds = [
            component
            for component in self.components.values()
            if component.GetFieldText("PartKey") == "SK9822"
        ]
        for led in leds:
            self._required_net(led.GetReference(), Sk9822Pin.FIVE_VOLTS, "+5V")
            self._required_net(led.GetReference(), Sk9822Pin.GROUND, "GND")
        led_count = len(leds)
        brightness = Fraction(1) if full_white else self.led_brightness_max
        return BOARD_POWER.host_and_logic_amps + (
            led_count * BOARD_POWER.led_full_white_amps_each * float(brightness)
        )

    def _power(self, full_white: bool) -> str:
        dc_input, dc_fused, five_volts = self._power_path_nets()
        input_node = _node(dc_input)
        fused_node = _node(dc_fused)
        rail_node = _node(five_volts)
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
            f"VINPUT {input_node} 0 {BOARD_POWER.supply_volts}",
            f"RFUSE {input_node} {fused_node} {BOARD_POWER.path_ohms / 2}",
            f"RSWITCH {fused_node} {rail_node} {BOARD_POWER.path_ohms / 2}",
            f"ILOAD {rail_node} 0 {load}",
            ".tran 1u 10u",
            f".meas tran result_5v FIND v({rail_node}) AT=5u",
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
                circuit.controls.extend(
                    (f"let {prefix}={expression.strip(chr(39))}", f"print {prefix}")
                )
            elif row.startswith(".meas "):
                circuit.controls.append(row.removeprefix("."))
            else:
                circuit.rows.append(row)
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
