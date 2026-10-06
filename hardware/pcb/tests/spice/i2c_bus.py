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
