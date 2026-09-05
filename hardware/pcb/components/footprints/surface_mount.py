"""Compatibility exports for component-owned surface-mount land patterns."""

from components.ahct125 import AHCT125_SOIC
from components.capacitor import CAPACITOR_0603, CAPACITOR_0805
from components.fuse import FUSE_2410
from components.hall_sensor import HALL_SOT23
from components.tca9554 import TCA9554_SOIC
from components.test_point import TEST_POINT_SMD
from components.tvs_diode import TVS_SMB

__all__ = (
    "AHCT125_SOIC",
    "CAPACITOR_0603",
    "CAPACITOR_0805",
    "FUSE_2410",
    "HALL_SOT23",
    "TCA9554_SOIC",
    "TEST_POINT_SMD",
    "TVS_SMB",
)
