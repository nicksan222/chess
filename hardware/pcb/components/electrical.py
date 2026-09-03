"""Reviewed electrical characteristics shared by SPICE capability tests.

Connectivity and fitted values still come from ``BoardDesign``. These values are
only the data-sheet or system-level characteristics that KiCad cannot express.
Keeping them here prevents individual simulations from inventing component
behaviour independently.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VoltageRange:
    minimum: float
    maximum: float

    def tuple(self) -> tuple[float, float]:
        return self.minimum, self.maximum


@dataclass(frozen=True)
class LogicModel:
    supply_volts: float
    low: VoltageRange
    high: VoltageRange


@dataclass(frozen=True)
class HallSensorModel:
    output_on_ohms: float
    output_off_spice: str
    input_pullup_ohms: float
    magnetic_drive_threshold_volts: float
    magnetic_drive_hysteresis_volts: float


@dataclass(frozen=True)
class Ahct125Model:
    supply_volts: float
    minimum_supply_volts: float
    enable_low_max_volts: float
    input_high_threshold_volts: float
    output_headroom_volts: float
    low: VoltageRange
    high: VoltageRange


@dataclass(frozen=True)
class BoardPowerModel:
    supply_volts: float
    path_ohms: float
    host_and_logic_amps: float
    led_full_white_amps_each: float
    load_soft_start_volts: float
    current_tolerance_amps: float
    healthy_rail: VoltageRange
    overloaded_rail: VoltageRange
    off_rail: VoltageRange


LOGIC_3V3 = LogicModel(
    supply_volts=3.3,
    low=VoltageRange(0.0, 0.1),
    high=VoltageRange(3.2, 3.4),
)
HALL_SENSOR = HallSensorModel(
    output_on_ohms=50.0,
    output_off_spice="1T",
    input_pullup_ohms=100_000.0,
    magnetic_drive_threshold_volts=1.65,
    magnetic_drive_hysteresis_volts=0.1,
)
PI_GPIO_PULLUP_OHMS = 50_000.0
AHCT125 = Ahct125Model(
    supply_volts=5.0,
    minimum_supply_volts=4.5,
    enable_low_max_volts=0.8,
    input_high_threshold_volts=2.0,
    output_headroom_volts=0.1,
    low=VoltageRange(0.0, 0.3),
    high=VoltageRange(4.5, 5.1),
)
BOARD_POWER = BoardPowerModel(
    supply_volts=5.0,
    path_ohms=0.12,
    host_and_logic_amps=0.45,
    led_full_white_amps_each=0.060,
    load_soft_start_volts=0.2,
    current_tolerance_amps=0.01,
    healthy_rail=VoltageRange(4.75, 5.1),
    overloaded_rail=VoltageRange(4.3, 4.63),
    off_rail=VoltageRange(0.0, 0.01),
)
