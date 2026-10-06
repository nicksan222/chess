"""Independent pin-level expectations for the generated native board.

Role: checks the *generated* `netlist.json` (from `PCB_OUTPUT` if set, else
`generated/`) against golden values written out by hand below. The tables are
deliberately not imported from `shared/` or the assemblies: if a mapping were wrong
in both the code and its own test data, the same mistake could never be caught. Here
a change to bank membership, LED order, button pins or supply wiring must be made
twice, on purpose. Evidence type: software test of generated connectivity only; it
does not show the real parts, footprints or board work electrically.

Reference designators used: J1 Pi header, J2 display harness header, J4 power-entry
harness header (panel jack + rocker; J3/SW13 retired), F1 fuse, D1 TVS across
+5V/GND, U5 LED-data buffer with R9 series termination (R1/R2 retired in S5:
the Pi's own I2C pull-ups suffice),
TP* test points, U1-U4/U70-U73 Hall-bank expanders (see `bank_assemblies.py`).
"""

import os
import unittest
from itertools import pairwise
from pathlib import Path
from typing import ClassVar, TypedDict, cast

from shared.json_values import parse_json

# Left rank-turn data terminators (S5), by driving square.
TURN_TERMINATORS = {"A2": "R10", "A4": "R11", "A6": "R12"}
PCB_ROOT = Path(__file__).resolve().parents[2]
EXPANDER_INPUT_PINS = ("4", "5", "6", "7", "9", "10", "11", "12")
BANKS = (
    ("U1", "0x20", "A1 B1 A2 B2 C1 D1 C2 D2"),
    ("U2", "0x21", "E1 F1 E2 F2 G1 H1 G2 H2"),
    ("U3", "0x22", "A3 B3 A4 B4 C3 D3 C4 D4"),
    ("U4", "0x23", "E3 F3 E4 F4 G3 H3 G4 H4"),
    ("U70", "0x24", "A5 B5 A6 B6 C5 D5 C6 D6"),
    ("U71", "0x25", "E5 F5 E6 F6 G5 H5 G6 H6"),
    ("U72", "0x26", "A7 B7 A8 B8 C7 D7 C8 D8"),
    ("U73", "0x27", "E7 F7 E8 F8 G7 H7 G8 H8"),
)
LED_ORDER = """
    A1 B1 C1 D1 E1 F1 G1 H1 H2 G2 F2 E2 D2 C2 B2 A2
    A3 B3 C3 D3 E3 F3 G3 H3 H4 G4 F4 E4 D4 C4 B4 A4
    A5 B5 C5 D5 E5 F5 G5 H5 H6 G6 F6 E6 D6 C6 B6 A6
    A7 B7 C7 D7 E7 F7 G7 H7 H8 G8 F8 E8 D8 C8 B8 A8
""".split()  # noqa: SIM905 - compact, reviewable golden data
BUTTONS = (
    ("UP", "SW1", "29"),
    ("DOWN", "SW2", "31"),
    ("LEFT", "SW3", "32"),
    ("RIGHT", "SW4", "33"),
    ("OK", "SW5", "36"),
    ("RESET", "SW6", "11"),
    ("PASS", "SW7", "35"),
    ("F1", "SW8", "38"),
    ("F2", "SW9", "40"),
    ("F3", "SW10", "15"),
    ("F4", "SW11", "16"),
    ("F5", "SW12", "18"),
)


class PartRecord(TypedDict):
    part_key: str
    extras: dict[str, str]


class BoardRecord(TypedDict):
    components: dict[str, PartRecord]
    nets: dict[str, list[list[str]]]


class NetlistRecord(TypedDict):
    projects: dict[str, BoardRecord]


class BoardContractTest(unittest.TestCase):
    components: ClassVar[dict[str, PartRecord]]
    nets: ClassVar[dict[str, set[tuple[str, str]]]]
    endpoint_net: ClassVar[dict[tuple[str, str], str]]

    @classmethod
    def setUpClass(cls) -> None:
        output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
        record = cast(NetlistRecord, parse_json((output / "netlist.json").read_text()))
        board = record["projects"]["board"]
        cls.components = board["components"]
        cls.nets = {
            name: {(endpoint[0], endpoint[1]) for endpoint in endpoints}
            for name, endpoints in board["nets"].items()
        }
        cls.endpoint_net = {
            endpoint: name
            for name, endpoints in cls.nets.items()
            for endpoint in endpoints
        }

    def assert_net(self, name: str, *endpoints: tuple[str, str]) -> None:
        self.assertEqual(self.nets.get(name), set(endpoints), name)

    def test_each_hall_square_reaches_its_designated_expander_input(self) -> None:
        sensors = {
            part["extras"]["Square"]: reference
            for reference, part in self.components.items()
            if part["part_key"] == "HALL_SENSOR"
        }
        self.assertEqual(len(sensors), 64)
        for reference, address, squares in BANKS:
            with self.subTest(bank=reference):
                self.assertEqual(
                    self.components[reference]["extras"]["Address"], address
                )
                for bit, square in enumerate(squares.split()):
                    self.assert_net(
                        f"SQ_{square}",
                        (sensors[square], "2"),
                        (reference, EXPANDER_INPUT_PINS[bit]),
                    )
                for bit, pin in enumerate(("1", "2", "3")):
                    expected = (
                        "+3V3" if (int(address, 16) - 0x20) & (1 << bit) else "GND"
                    )
                    self.assertEqual(self.endpoint_net[(reference, pin)], expected)

    def test_led_data_and_clock_follow_all_64_squares_in_order(self) -> None:
        leds = {
            part["extras"]["Square"]: reference
            for reference, part in self.components.items()
            if part["part_key"] == "SK9822"
        }
        self.assertEqual(set(leds), set(LED_ORDER))
        self.assert_net("SPI_DATA_3V3", ("J1", "19"), ("U5", "2"))
        self.assert_net("SPI_CLK_3V3", ("J1", "23"), ("U5", "5"))
        self.assert_net("LED_DATA_5V", ("U5", "3"), (leds["A1"], "1"), ("TP3", "1"))
        self.assert_net("LED_CLK_5V", ("U5", "6"), (leds["A1"], "2"), ("TP4", "1"))
        for index, (left, right) in enumerate(pairwise(LED_ORDER)):
            with self.subTest(link=index + 1):
                self.assertEqual(
                    self.components[leds[left]]["extras"]["ChainIndex"], str(index + 1)
                )
                for output_pin, input_pin in (("6", "1"), ("5", "2")):
                    net = self.endpoint_net[(leds[left], output_pin)]
                    self.assert_net(
                        net, (leds[left], output_pin), (leds[right], input_pin)
                    )
        self.assertEqual(self.components[leds["A8"]]["extras"]["ChainIndex"], "64")
        self.assertNotIn((leds["A8"], "6"), self.endpoint_net)
        self.assertNotIn((leds["A8"], "5"), self.endpoint_net)

    def test_host_bus_and_button_pins_reach_the_right_devices(self) -> None:
        expanders = [(reference, "15") for reference, _, _ in BANKS]
        self.assert_net(
            "I2C_SDA", ("J1", "3"), ("J2", "4"), ("R1", "2"), ("TP7", "1"), *expanders
        )
        self.assert_net(
            "I2C_SCL",
            ("J1", "5"),
            ("J2", "3"),
            ("R2", "2"),
            ("TP6", "1"),
            *((reference, "14") for reference, _, _ in BANKS),
        )
        for name, switch, header_pin in BUTTONS:
            with self.subTest(button=name):
                self.assert_net(f"BTN_{name}", ("J1", header_pin), (switch, "1"))

    def test_input_protection_and_supply_polarity(self) -> None:
        self.assertEqual(self.components["F1"]["part_key"], "FUSE_2A")
        self.assert_net("DC_IN", ("J3", "1"), ("F1", "1"))
        self.assert_net("DC_FUSED", ("F1", "2"), ("SW13", "1"))
        for endpoint in (("SW13", "2"), ("D1", "1"), ("J1", "2"), ("J1", "4")):
            self.assertEqual(self.endpoint_net[endpoint], "+5V")
        for endpoint in (("J3", "2"), ("J3", "3"), ("D1", "2")):
            self.assertEqual(self.endpoint_net[endpoint], "GND")
