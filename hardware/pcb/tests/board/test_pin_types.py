"""No floating CMOS input, no undriven open-drain net, rails on rail pins.

Pin electrical types are hand-typed from the datasheets cited in
`test_land_patterns.py`: TI SCPS233E §5 (TCA9554: P-ports push-pull I/O with an
internal 100 kOhm pull-up, INT and SDA open-drain), TI SCLS264R Table 4-1 and note
"all unused inputs must be held at VCC or GND" (SN74AHCT125: nOE active-low input),
TI SLVSDC7H Table 4-1 (DRV5032FC: open-drain output), Opsco SPC/SK9822-A §5 and the
Raspberry Pi 40-pin header (GPIO, 3V3 output, 5V input). Parts without logic pins
(passives, switches, connectors to off-board modules) are passive.
"""

import unittest
from collections.abc import Collection, Mapping, Sequence
from typing import ClassVar

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from pcb.definition.verification import ASSUMPTIONS

INPUT = "input"
OUTPUT = "output"
TRISTATE = "tristate output"
OPEN_DRAIN = "open-drain output"
IO_PULLUP = "I/O with internal pull-up"
HOST_GPIO = "host GPIO"
POWER = "power input"
POWER_OUT = "power output"
GROUND = "ground"
# Analog pin set by an external resistor or capacitor (TPS25947 EN/UVLO, OVLO,
# PGTH, ILM, DVDT, ITIMER: "Do not leave floating", SLVSFC9C Table 5-1).
ANALOG = "analog, set by an external R or C"

RAILS = frozenset({"+5V", "+3V3", "LED_5V"})

PIN_TYPES: Mapping[str, Mapping[str, str]] = {
    "SK9822": {
        "1": INPUT,
        "2": INPUT,
        "3": GROUND,
        "4": POWER,
        "5": OUTPUT,
        "6": OUTPUT,
    },
    "TCA9554": {
        "1": INPUT,
        "2": INPUT,
        "3": INPUT,
        **{pin: IO_PULLUP for pin in ("4", "5", "6", "7", "9", "10", "11", "12")},
        "8": GROUND,
        "13": OPEN_DRAIN,
        "14": INPUT,
        "15": OPEN_DRAIN,
        "16": POWER,
    },
    "AHCT125": {
        **{pin: INPUT for pin in ("1", "2", "4", "5", "9", "10", "12", "13")},
        **{pin: TRISTATE for pin in ("3", "6", "8", "11")},
        "7": GROUND,
        "14": POWER,
    },
    "HALL_SENSOR": {"1": POWER, "2": OPEN_DRAIN, "3": GROUND},
    # TI SLVSFC9C Table 5-1 (TPS259474ARPW): PG open-drain, IN supply, OUT output.
    "EFUSE": {
        **{pin: ANALOG for pin in ("1", "2", "4", "7", "9", "10")},
        "3": OPEN_DRAIN,
        "5": POWER,
        "6": POWER_OUT,
        "8": GROUND,
    },
    # S6 LED switch: Vishay Si4403DDY (1-3 S, 4 G, 5-8 D); onsemi BSS138LT1G
    # (1 G, 2 S, 3 D). Q1's gate is set by R16/C145; Q2's drain is open-drain.
    "LED_SWITCH": {
        **{pin: POWER for pin in ("1", "2", "3")},
        "4": ANALOG,
        **{pin: POWER_OUT for pin in ("5", "6", "7", "8")},
    },
    "LED_SWITCH_DRIVER": {"1": INPUT, "2": GROUND, "3": OPEN_DRAIN},
    # TI SN74LVC1G97 DBV (S6b H6): In1 (tied high), In0, In2 inputs; Y push-pull.
    "LED_ENABLE_GATE": {
        "1": INPUT,
        "2": GROUND,
        "3": INPUT,
        "4": OUTPUT,
        "5": POWER,
        "6": INPUT,
    },
    "PI_ZERO_HEADER": {
        **{str(pin): HOST_GPIO for pin in range(1, 41)},
        "1": POWER_OUT,
        "17": POWER_OUT,
        "2": POWER,
        "4": POWER,
        **{str(pin): GROUND for pin in (6, 9, 14, 20, 25, 30, 34, 39)},
    },
}
DRIVERS = frozenset({OUTPUT, TRISTATE, HOST_GPIO, POWER_OUT})
PUSH_PULL = frozenset({OUTPUT, TRISTATE})
MAY_FLOAT = frozenset({OUTPUT, TRISTATE, OPEN_DRAIN, IO_PULLUP, HOST_GPIO})
# Passive parts that can set an ANALOG pin.
SETTING_PREFIXES = ("RES_", "CAP_")
# Supply pins and the rail each must sit on (same datasheets as above).
POWER_RAILS: Mapping[tuple[str, str], str] = {
    ("SK9822", "4"): "LED_5V",
    ("TCA9554", "16"): "+3V3",
    ("AHCT125", "14"): "+5V",
    ("HALL_SENSOR", "1"): "+3V3",
    ("PI_ZERO_HEADER", "2"): "+5V",
    ("PI_ZERO_HEADER", "4"): "+5V",
    ("PI_ZERO_HEADER", "1"): "+3V3",
    ("PI_ZERO_HEADER", "17"): "+3V3",
    ("EFUSE", "5"): "DC_FUSED",
    ("EFUSE", "6"): "+5V",
    **{("LED_SWITCH", pin): "+5V" for pin in ("1", "2", "3")},
    **{("LED_SWITCH", pin): "LED_5V" for pin in ("5", "6", "7", "8")},
    ("LED_ENABLE_GATE", "5"): "+5V",
}
# Raspberry Pi documentation: GPIO2/3 (header pins 3/5) carry fixed 1.8 kOhm pull-ups.
# Any other host GPIO is biased only by firmware.
HOST_PULLED_PINS = frozenset({"3", "5"})
# Host pins the firmware drives push-pull (SPI0 MOSI/SCLK, spidev; S6 LED_EN on
# pin 37, a typed output in pins.rs): they count as drivers.
HOST_PUSH_PULL_PINS = frozenset({"19", "23", "37"})
# Parts with no logic pins (passives, switches, test points, off-board connectors).
PASSIVE_KEYS = frozenset(
    {
        "BUTTON",
        "CAP_100N",
        "CAP_10U",
        "CAP_560U",
        "FUSE_2A",
        "OLED_HEADER",
        "POWER_HEADER",
        "RES_1K",
        "RES_10K",
        "RES_56",
        "RES_100K",
        "TEST_POINT",
        "TVS_12V0",
        "RES_1K65",
        "RES_261K",
        "RES_604K_PRECISION",
        "RES_169K_PRECISION",
        "CAP_10N",
        "CAP_1N",
        "CAP_1U",
    }
)

Endpoint = tuple[str, str]
# Series resistors (S5 R9-R12 terminations; S6 R13 LED_EN to Q2's gate, R16 LED_EN_N
# to Q1's gate): the net past one is driven by its source.
SERIES_KEYS = frozenset({"RES_56", "RES_1K", "RES_100K"})


def electrical_findings(
    nets: Mapping[str, Sequence[Endpoint]],
    part_keys: Mapping[str, str],
    assumptions: Collection[str] = ASSUMPTIONS,
) -> list[str]:
    """Floating inputs, undriven open-drain nets, contention, misplaced rail pins."""
    findings: list[str] = []
    net_of = {end: name for name, ends in nets.items() for end in ends}
    driven = {
        name
        for name, ends in nets.items()
        for reference, pin in ends
        if PIN_TYPES.get(part_keys.get(reference, ""), {}).get(pin) in PUSH_PULL
        or (part_keys.get(reference) == "PI_ZERO_HEADER" and pin in HOST_PUSH_PULL_PINS)
    }
    # A resistor from the net to a rail (S6 R15 on LED_EN_N) is a pull-up; an
    # open-drain net with one is driven both ways.
    resistor_pulled = {
        name
        for name, ends in nets.items()
        for reference, pin in ends
        if part_keys.get(reference, "").startswith("RES_")
        and net_of.get((reference, "2" if pin == "1" else "1")) in RAILS
    }
    driven |= {
        name
        for name in resistor_pulled
        if any(
            PIN_TYPES.get(part_keys.get(reference, ""), {}).get(pin) == OPEN_DRAIN
            for reference, pin in nets[name]
        )
    }
    for name, endpoints in nets.items():
        series_driven = any(
            net_of.get((reference, "2" if pin == "1" else "1")) in driven
            for reference, pin in endpoints
            if part_keys.get(reference) in SERIES_KEYS
        )
        typed = [
            (reference, pin, PIN_TYPES[part_keys[reference]][pin])
            for reference, pin in endpoints
            if part_keys.get(reference) in PIN_TYPES
        ]
        kinds = {kind for _, _, kind in typed}
        label = ", ".join(f"{r}-{p}" for r, p, _ in typed)
        for reference, pin, kind in typed:
            expected = POWER_RAILS.get((part_keys[reference], pin))
            if kind in {POWER, POWER_OUT} and name != expected:
                findings.append(
                    f"{reference}-{pin} power pin on {name}, not {expected}"
                )
            if kind == GROUND and name != "GND":
                findings.append(f"{reference}-{pin} ground pin on {name}")
        if name.startswith("unconnected-"):
            findings.extend(
                f"{reference}-{pin} {kind} left unconnected"
                for reference, pin, kind in typed
                if kind not in MAY_FLOAT
            )
            continue
        if name in RAILS or name == "GND":
            continue
        drivers = [
            f"{r}-{p}"
            for r, p, kind in typed
            if kind in PUSH_PULL or (kind == HOST_GPIO and p in HOST_PUSH_PULL_PINS)
        ]
        if len(drivers) > 1:
            findings.append(f"{name}: contention between {', '.join(drivers)}")
        host_pulled = any(
            kind == HOST_GPIO and pin in HOST_PULLED_PINS for _, pin, kind in typed
        )
        pulled = IO_PULLUP in kinds or host_pulled or name in resistor_pulled
        if INPUT in kinds and not (
            kinds & DRIVERS or series_driven or (OPEN_DRAIN in kinds and pulled)
        ):
            findings.append(f"{name}: input without a driver ({label})")
        if ANALOG in kinds and not any(
            part_keys.get(reference, "").startswith(SETTING_PREFIXES)
            for reference, _ in endpoints
        ):
            findings.append(f"{name}: analog pin without its setting part ({label})")
        if OPEN_DRAIN in kinds and not pulled:
            findings.append(f"{name}: open-drain without a pull-up ({label})")
        switched = any(
            part_keys.get(reference) == "BUTTON" for reference, _ in endpoints
        )
        if (
            switched
            and HOST_GPIO in kinds
            and not pulled
            and "Pi GPIO pull-ups" not in assumptions
        ):
            findings.append(
                f"{name}: switch input relies on an unrecorded firmware bias"
            )
    return sorted(findings)


class PinTypeTest(unittest.TestCase):
    """Electrical pin types against the board's nets (see the module docstring for the rules)."""

    nets: ClassVar[dict[str, tuple[Endpoint, ...]]]
    part_keys: ClassVar[dict[str, str]]

    @classmethod
    def setUpClass(cls) -> None:
        """Build the board once and index its parts and nets."""
        native_board = board.load()
        cls.part_keys = {
            footprint.GetReference(): footprint.GetFieldText("PartKey")
            for footprint in native.parts(native_board)
        }
        cls.nets = {
            name: tuple((str(ref), str(pin)) for ref, pin in endpoints)
            for name, endpoints in native.connections(native_board).items()
        }

    def test_every_typed_pin_is_known_to_its_datasheet_table(self) -> None:
        for name, endpoints in self.nets.items():
            for reference, pin in endpoints:
                key = self.part_keys[reference]
                if key in PIN_TYPES:
                    with self.subTest(net=name, pin=f"{reference}-{pin}"):
                        self.assertIn(pin, PIN_TYPES[key])

    def test_board_has_no_floating_input_or_undriven_open_drain(self) -> None:
        self.assertEqual(electrical_findings(self.nets, self.part_keys), [])

    def test_unused_buffer_channels_are_disabled_and_tied(self) -> None:
        # SCLS264R: nOE is active-low, so an unused channel's OE goes high (+5V).
        rail = {endpoint: name for name, ends in self.nets.items() for endpoint in ends}
        buffer = next(r for r, k in self.part_keys.items() if k == "AHCT125")
        # S6b: channels 1-2 are enabled by LED_OE_N (U75: low only once LED_5V is
        # up), so their outputs are Hi-Z whenever the chain is not fully powered.
        for pin, net in (
            ("1", "LED_OE_N"),
            ("4", "LED_OE_N"),
            ("10", "+5V"),
            ("13", "+5V"),
        ):
            with self.subTest(pin=pin):
                self.assertEqual(rail[(buffer, pin)], net)
        for pin in ("9", "12"):
            with self.subTest(pin=pin):
                self.assertIn(rail[(buffer, pin)], RAILS | {"GND"})

    def test_every_catalogue_part_is_typed_or_declared_passive(self) -> None:
        self.assertEqual(set(PIN_TYPES) | PASSIVE_KEYS, set(PCB_PARTS))
        self.assertFalse(set(PIN_TYPES) & PASSIVE_KEYS)

    def test_checker_reports_contention_wrong_rail_and_unrecorded_bias(self) -> None:
        nets = {name: list(ends) for name, ends in self.nets.items()}
        leds = sorted(r for r, k in self.part_keys.items() if k == "SK9822")
        data = next(name for name, ends in nets.items() if (leds[0], "6") in ends)
        nets[data].append((leds[1], "6"))
        nets["LED_5V"].remove((leds[2], "4"))
        nets["+3V3"].append((leds[2], "4"))
        findings = electrical_findings(nets, self.part_keys, assumptions=())
        self.assertTrue(any("contention" in f for f in findings))
        self.assertIn(f"{leds[2]}-4 power pin on +3V3, not LED_5V", findings)
        self.assertTrue(any("unrecorded firmware bias" in f for f in findings))

    def test_checker_reports_a_floating_input_and_a_missing_pull_up(self) -> None:
        nets = {name: list(ends) for name, ends in self.nets.items()}
        buffer = next(r for r, k in self.part_keys.items() if k == "AHCT125")
        nets["GND"].remove((buffer, "9"))
        nets[f"unconnected-({buffer}-Pad9)"] = [(buffer, "9")]
        expander = next(r for r, k in self.part_keys.items() if k == "TCA9554")
        sda = next(name for name, ends in nets.items() if (expander, "15") in ends)
        nets[sda] = [
            end for end in nets[sda] if self.part_keys.get(end[0]) != "PI_ZERO_HEADER"
        ]
        efuse = next(r for r, k in self.part_keys.items() if k == "EFUSE")
        limit = next(name for name, ends in nets.items() if (efuse, "9") in ends)
        nets[limit] = [(efuse, "9")]
        # R9 open: the LED data past it has no source.
        series = "R9"
        self.assertIn(self.part_keys[series], SERIES_KEYS)
        buffered = next(name for name, ends in nets.items() if (series, "2") in ends)
        nets[buffered] = [end for end in nets[buffered] if end[0] != series]
        findings = electrical_findings(nets, self.part_keys)
        self.assertIn(f"{buffer}-9 input left unconnected", findings)
        self.assertTrue(any("open-drain without a pull-up" in f for f in findings))
        self.assertTrue(
            any("LED_DATA_5V: input without a driver" in f for f in findings)
        )
        self.assertTrue(
            any("analog pin without its setting part" in f for f in findings)
        )

    def test_led_enable_node_needs_its_pull_up_and_single_driver(self) -> None:
        # S6: LED_EN_N (Q2 open drain, R15 to +5V) drives U5's 1OE/2OE and Q1's
        # gate. Without R15 it floats (buffer and switch undefined); a second
        # push-pull source on LED_EN (pin 37's net) is contention.
        nets = {name: list(ends) for name, ends in self.nets.items()}
        nets["LED_EN_N"] = [end for end in nets["LED_EN_N"] if end[0] != "R15"]
        nets["LED_EN"].append(("U5", "3"))
        findings = electrical_findings(nets, self.part_keys)
        self.assertIn("LED_EN_N: open-drain without a pull-up (Q2-3, U75-1)", findings)
        self.assertTrue(any(f.startswith("LED_EN: contention") for f in findings))


if __name__ == "__main__":
    unittest.main()
