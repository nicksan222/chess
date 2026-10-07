"""The off-board wiring harnesses: one definition for tests, BOM and assembly.

Each wire is fixed by the connector cavity it is crimped into. A JST cavity mates
the header circuit of the same number, counted the way JST's drawings count them
(VH catalogue p4, SH catalogue p1), so physical cavity k lands on board pad k only
while the footprint keeps the drawing's chirality (pcb tests/board/test_harness).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from shared.components import (
    COMPONENTS,
    OLED_HARNESS_WIRES,
    POWER_HARNESS_WIRES,
    ComponentSpec,
)
from shared.components.harness import OLED_WIRE_LENGTH_MM, POWER_WIRE_LENGTH_MM

from .barrel_jack import BarrelJackPin
from .connectors import OledHeaderPin
from .passives import PowerSwitchPin
from .power_header import PowerHeaderPin


@dataclass(frozen=True)
class HarnessWire:
    """One wire of a harness, fixed by the connector cavity it is crimped into, with its net, colour, gauge, length and far end."""

    connector: str  # Board reference of the header the housing plugs into.
    cavity: str  # JST cavity number == header circuit number it mates.
    net: str  # Board net that circuit must carry.
    colour: str
    gauge_awg: int
    length_mm: float
    far_part: str  # Component key at the far end.
    far_terminal: str  # Terminal name there, as the part's drawing labels it.
    far_termination: str  # How the wire is attached at the far end.

    @property
    def wire(self) -> ComponentSpec:
        """The bought wire of this gauge and colour (one BOM line per colour)."""
        return {18: POWER_HARNESS_WIRES, 28: OLED_HARNESS_WIRES}[self.gauge_awg][
            self.colour
        ]


# Interface S3a H1 + S3c H4 + S4b. Switchcraft 722A drawing "712A 722A 732A" rev J:
# terminals CENTER PIN, SLEEVE, SLEEVE SHUNT (shunt left open). Rocker RA11131100:
# function 1 Off-On, contact 2-1 (E-Switch RA1 catalog drawing 11/2/2022), two
# 4.80 x 0.80 mm tabs; an SPST contact is symmetric, so either tab serves. Since
# S4b the rocker switches DC_FUSED onto RUN (eFuse enable, ~1.1 mA wetting load),
# not the board's load current.
POWER_HARNESS = (
    HarnessWire(
        "J4",
        PowerHeaderPin.DC_INPUT,
        "DC_IN",
        "red",
        18,
        POWER_WIRE_LENGTH_MM,
        "BARREL_JACK",
        BarrelJackPin.CENTRE_POSITIVE,
        "solder lug",
    ),
    HarnessWire(
        "J4",
        PowerHeaderPin.GROUND,
        "GND",
        "black",
        18,
        POWER_WIRE_LENGTH_MM,
        "BARREL_JACK",
        BarrelJackPin.SLEEVE_GROUND,
        "solder lug",
    ),
    HarnessWire(
        "J4",
        PowerHeaderPin.FUSED_TO_SWITCH,
        "DC_FUSED",
        "orange",
        18,
        POWER_WIRE_LENGTH_MM,
        "POWER_SWITCH",
        PowerSwitchPin.FUSED_INPUT,
        "FASTON 2-520275-2",
    ),
    HarnessWire(
        "J4",
        PowerHeaderPin.RUN,
        "RUN",
        "white",
        18,
        POWER_WIRE_LENGTH_MM,
        "POWER_SWITCH",
        PowerSwitchPin.RUN_OUTPUT,
        "FASTON 2-520275-2",
    ),
)

# J2 to MC242GW's factory-I2C GND/VCC/SCL/SDA pads, soldered; RES stays open.
OLED_HARNESS = tuple(
    HarnessWire(
        "J2",
        pin,
        net,
        colour,
        28,
        OLED_WIRE_LENGTH_MM,
        "OLED_MODULE",
        label,
        "solder to pad",
    )
    for pin, net, colour, label in (
        (OledHeaderPin.GROUND, "GND", "black", "GND"),
        (OledHeaderPin.THREE_VOLTS_THREE, "+3V3", "red", "VCC"),
        (OledHeaderPin.I2C_CLOCK, "I2C_SCL", "yellow", "SCL"),
        (OledHeaderPin.I2C_DATA, "I2C_SDA", "blue", "SDA"),
    )
)

HARNESSES = {"Power entry": POWER_HARNESS, "OLED": OLED_HARNESS}

# Bought parts each harness is made from, with the quantity one board needs:
# connector parts here, plus one line per wire colour taken from the wires.
_CONNECTOR_PARTS = {
    "Power entry": {
        "POWER_HARNESS_HOUSING": 1,
        "POWER_HARNESS_CONTACT": 4,
        "ROCKER_RECEPTACLE": 2,
    },
    "OLED": {"OLED_HARNESS_HOUSING": 1, "OLED_HARNESS_CONTACT": 4},
}
HARNESS_PARTS = {
    name: _CONNECTOR_PARTS[name]
    | {
        key: sum(w.wire.key == key for w in wires)
        for key in dict.fromkeys(w.wire.key for w in wires)
    }
    for name, wires in HARNESSES.items()
}

# The SPST rocker's two tabs are interchangeable; say so on the assembly table.
TERMINAL_LABELS: dict[tuple[str, str], str] = {
    ("POWER_SWITCH", PowerSwitchPin.FUSED_INPUT): "either tab",
    ("POWER_SWITCH", PowerSwitchPin.RUN_OUTPUT): "other tab",
}


def render_harness_table() -> str:
    """Markdown assembly table (written to generated/harness.md by the build)."""
    lines = [
        "# Harness wiring",
        "",
        "Generated from `hardware/shared/electronics/harness.py`; do not edit.",
        "Cavity numbers are JST's: cavity k mates header circuit k.",
        "",
    ]
    for name, wires in HARNESSES.items():
        lines.extend(
            (
                f"## {name}",
                "",
                "| Header | Cavity | Net | Wire | Far end | Terminal | Attach |",
                "|---|---|---|---|---|---|---|",
            )
        )
        for w in wires:
            spec = COMPONENTS[w.far_part]
            terminal = TERMINAL_LABELS.get((w.far_part, w.far_terminal), w.far_terminal)
            lines.append(
                f"| {w.connector} | {w.cavity} | {w.net} | {w.colour} {w.gauge_awg} "
                f"AWG {w.length_mm:g} mm | {spec.manufacturer} {spec.mpn} | "
                f"{terminal} | {w.far_termination} |"
            )
        lines.append("")
        lines.extend(
            f"- {COMPONENTS[key].kit_quantity(quantity)} {COMPONENTS[key].manufacturer} "
            f"{COMPONENTS[key].mpn}: {COMPONENTS[key].description} "
            f"(bought: {COMPONENTS[key].purchase_unit})"
            for key, quantity in HARNESS_PARTS[name].items()
        )
        lines.append("")
    return "\n".join(lines)


# Bought terminal roles, independent of the wire's declared net. RES and the
# jack's switched sleeve deliberately have no harness connection.
HARNESS_TERMINAL_NETS = {
    ("BARREL_JACK", BarrelJackPin.CENTRE_POSITIVE): "DC_IN",
    ("BARREL_JACK", BarrelJackPin.SLEEVE_GROUND): "GND",
    ("POWER_SWITCH", PowerSwitchPin.FUSED_INPUT): "DC_FUSED",
    ("POWER_SWITCH", PowerSwitchPin.RUN_OUTPUT): "RUN",
    ("OLED_MODULE", "GND"): "GND",
    ("OLED_MODULE", "VCC"): "+3V3",
    ("OLED_MODULE", "SCL"): "I2C_SCL",
    ("OLED_MODULE", "SDA"): "I2C_SDA",
}


def validate_harness_connections(
    pin_nets: Mapping[tuple[str, str], str], wires: Iterable[HarnessWire]
) -> None:
    """Close each wire against the actual board pin and bought terminal role."""
    cavities: set[tuple[str, str]] = set()
    terminals: set[tuple[str, str]] = set()
    for wire in wires:
        cavity = (wire.connector, wire.cavity)
        if cavity in cavities:
            raise ValueError(f"duplicate harness cavity: {cavity}")
        cavities.add(cavity)
        if pin_nets.get(cavity) != wire.net:
            raise ValueError(f"{cavity}: board net does not match {wire.net}")
        terminal = (wire.far_part, wire.far_terminal)
        if terminal in terminals:
            raise ValueError(f"duplicate harness far terminal: {terminal}")
        terminals.add(terminal)
        if HARNESS_TERMINAL_NETS.get(terminal) != wire.net:
            raise ValueError(f"{cavity}: far terminal does not carry {wire.net}")
    if terminals != set(HARNESS_TERMINAL_NETS):
        raise ValueError("harness far terminals are incomplete")
