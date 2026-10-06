"""I2C bus (SDA/SCL) from the routed board: capacitance, pull-ups, speed limits.

Since S5 the only on-board pull-ups are the Pi's own (Zero 2 W R23/R24 1.8 kOhm);
the OLED module may add its own (verification ASSUMPTION "OLED pull-ups": >= 4.7
kOhm or none). The bus capacitance is the routed copper (`bus_lines`), every
expander's Ci/Cio maximum, the Pi pin, and the module, harness and connector
allowances. Rise time is the 30-70 % time of an RC charge, 0.8473 R C (UM10204 7.1);
the low level is the expander's guaranteed sink point (3 mA at 0.4 V).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pcbnew

from shared import wiring
from spice import datasheets
from spice.board_harness import BoardHarness
from spice.bus_lines import net_copper
from spice.circuit import SpiceCircuit

REPOSITORY = Path(__file__).resolve().parents[4]
OLED_PULLUP_MIN_OHMS = 4700.0
HARNESS_METRES = 0.090


@dataclass(frozen=True)
class Bus:
    """One I2C net's total capacitance (farads) and the number of expanders on it."""

    net: str
    farads: float
    expanders: int


def firmware_i2c_hz(yocto: Path | None = None) -> int:
    """The I2C rate the firmware image configures (read-only, apps/firmware Yocto).

    The image enables the bus with meta-raspberrypi's ENABLE_I2C; an explicit
    `i2c_arm_baudrate` in the kas or layer config overrides the 100 kHz default.
    Comments (`#` to end of line) are ignored and the last assignment wins, as in
    BitBake (reviewer m7).
    """
    yocto = yocto or REPOSITORY / "apps/firmware/yocto"
    sources = [
        path
        for root in (yocto / "kas", yocto / "meta-firmware")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    lines = [
        line.split("#", 1)[0]
        for path in sources
        for line in path.read_text(errors="ignore").splitlines()
    ]
    text = "\n".join(lines)
    enabled: list[str] = re.findall(r'ENABLE_I2C\s*=\s*"(\d+)"', text)
    if not enabled or enabled[-1] != "1":
        raise ValueError("the firmware image does not enable the I2C bus")
    rates: list[str] = re.findall(r"i2c(?:_arm)?_baudrate\s*=\s*(\d+)", text)
    return int(rates[-1]) if rates else datasheets.PI_I2C_DEFAULT_HZ


class I2cBus:
    """Both I2C nets of a routed board, each with its estimated capacitance.

    Refuses a board that still has an on-board pull-up (the Pi's own are used since S5) or where
    any net does not reach all eight expanders, so a wiring change cannot be silently skipped.
    """

    def __init__(self, harness: BoardHarness, routed: pcbnew.BOARD) -> None:
        expanders = [
            reference
            for reference, component in harness.components.items()
            if component.GetFieldText("PartKey") == "TCA9554"
        ]
        self.buses: dict[str, Bus] = {}
        for net, per_device in (
            (wiring.SDA_NET, datasheets.TCA9554_SDA_FARADS),
            (wiring.SCL_NET, datasheets.TCA9554_SCL_FARADS),
        ):
            endpoints = harness.endpoints_by_net[net]
            keys = {harness.components[r].GetFieldText("PartKey") for r, _ in endpoints}
            if any(key.startswith("RES_") for key in keys):
                raise ValueError(
                    f"{net}: on-board pull-up found; the Pi's own are used (S5)"
                )
            on_bus = [r for r, _ in endpoints if r in expanders]
            if len(on_bus) != 8:
                raise ValueError(f"{net}: expected all eight expanders")
            farads = (
                net_copper(routed, net).farads
                + len(on_bus) * per_device
                + datasheets.PI_GPIO_INPUT_FARADS
                + datasheets.OLED_INPUT_FARADS
                + datasheets.HARNESS_FARADS_PER_M * HARNESS_METRES
                + datasheets.CONNECTOR_FARADS
            )
            self.buses[net] = Bus(net, farads, len(on_bus))

    @staticmethod
    def pullup_ohms(*, strongest: bool, oled_ohms: float | None) -> float:
        """Effective pull-up: the Pi's 1.8 kohm (lowest if `strongest`, else highest by its
        tolerance), in parallel with the OLED module's own pull-up when `oled_ohms` is given.
        """
        tolerance = datasheets.PI_I2C_PULLUP_TOLERANCE
        pi = datasheets.PI_I2C_PULLUP_OHMS * (
            1 - tolerance if strongest else 1 + tolerance
        )
        if oled_ohms is None:
            return pi
        return 1 / (1 / pi + 1 / oled_ohms)

    def rise_ns(self, net: str, *, oled_ohms: float | None) -> float:
        """Calculation cross-check: 30-70 % of an RC charge is 0.8473 R C."""
        ohms = self.pullup_ohms(strongest=False, oled_ohms=oled_ohms)
        return 0.8473 * ohms * self.buses[net].farads * 1e9

    def fastest_passing_hz(self) -> int:
        """Highest standard rate whose rise-time limit every corner meets."""
        worst = max(
            self.rise_ns(net, oled_ohms=oled)
            for net in self.buses
            for oled in OLED_CORNERS
        )
        passing = [hz for hz, limit in datasheets.I2C_RISE_NS.items() if worst <= limit]
        return max(passing, default=0)

    def edge(self, net: str, *, oled_ohms: float | None) -> SpiceCircuit:
        """Release from low (weakest pull-up) then sink at the guaranteed VOL point.

        The expander holds the line through 0.4 V / 3 mA (its datasheet VOL point as
        a resistance); `result_rise` is the 30-70 % time after release and
        `result_low` the held-low level with the strongest pull-up and VDD max.
        """
        rail = datasheets.RAIL_3V3_VOLTS
        weak = self.pullup_ohms(strongest=False, oled_ohms=oled_ohms)
        strong = self.pullup_ohms(strongest=True, oled_ohms=oled_ohms)
        sink = datasheets.I2C_VOL_VOLTS / datasheets.I2C_SINK_AMPS_AT_VOL
        farads = self.buses[net].farads
        circuit = SpiceCircuit(f"I2C {net} edge, OLED pull-up {oled_ohms}")
        circuit.rows.extend(
            (
                ".model SINK SW(Ron=1e-3 Roff=1e12 Vt=0.5 Vh=0.1)",
                f"VLO lo 0 {rail.low}",
                f"RW lo bus {weak}",
                f"CB bus 0 {farads}",
                "VREL rel 0 PULSE(1 0 1u 1n 1n 1 2)",
                "SREL bus 0 rel 0 SINK",
                f"VHI hi 0 {rail.high}",
                f"RS hi held {strong}",
                f"RSINK held 0 {sink}",
                ".tran 1n 12u",
            )
        )
        circuit.controls.extend(
            (
                f"meas tran t30 WHEN v(bus)={0.3 * rail.low} RISE=1",
                f"meas tran t70 WHEN v(bus)={0.7 * rail.low} RISE=1",
                "let result_rise = (t70 - t30) * 1e9",
                "meas tran result_low FIND v(held) AT=6u",
                "print result_rise result_low",
            )
        )
        return circuit


OLED_CORNERS: tuple[float | None, ...] = (None, OLED_PULLUP_MIN_OHMS)
"""OLED-module pull-up range (ASSUMPTION "OLED pull-ups"): absent, or >= 4.7 kOhm."""
