"""Pass bands and ideal control switches for the SPICE connectivity scenarios.

Not datasheet models (pushback-final, S6c). The button, bus and movement
scenarios are connectivity checks: each press, bus driver or magnet must reach
its own net and no other. They use ideal switches driven by a 0 / 3.3 V control
pulse and judge the result against wide 3.3 V pass bands. The datasheet-limited
cases are separate: Hall output levels (`hall_levels`, DRV5032 VOL and TCA9554
pull-ups), LED data levels (`level_shifter`), I2C edges (`test_i2c`) and the
button contacts themselves (TL1105 resistance in `datasheets.py`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoltageRange:
    """An inclusive (minimum, maximum) voltage window."""

    minimum: float
    maximum: float

    def tuple(self) -> tuple[float, float]:
        """The window as a (minimum, maximum) pair, for passing to `SpiceCircuit.expect`."""
        return self.minimum, self.maximum


@dataclass(frozen=True)
class LogicModel:
    """Logic levels of one supply: its voltage and the valid low and high output windows."""

    supply_volts: float
    low: VoltageRange
    high: VoltageRange


@dataclass(frozen=True)
class ControlSwitch:
    """An ideal SPICE switch closed by a control voltage, not a part model."""

    on_ohms: float
    off_spice: str
    drive_threshold_volts: float
    drive_hysteresis_volts: float


# Ideal 3.3 V source; asserted nets must sit within 0.1 V of ground and released
# ones within 0.1 V of the rail: a connectivity band, not a guaranteed VOL/VOH.
LOGIC_3V3 = LogicModel(
    supply_volts=3.3,
    low=VoltageRange(0.0, 0.1),
    high=VoltageRange(3.2, 3.4),
)

# The bus-input scenario's "asserted" driver: 50 Ohm against the Pi's 1.8 kOhm
# pull-up gives about 0.09 V, inside LOGIC_3V3.low. The threshold is half of the
# 0 / 3.3 V control pulse (magnet or press present), not a magnetic quantity; the
# Hall scenario uses the same drive with the DRV5032's datasheet VOL as Ron.
CONTROL_SWITCH = ControlSwitch(
    on_ohms=50.0,
    off_spice="1T",
    drive_threshold_volts=1.65,
    drive_hysteresis_volts=0.1,
)
