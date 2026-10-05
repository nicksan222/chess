"""Approved tca9554 product."""

from .spec import part

TCA9554 = part(
    "TCA9554",
    "8-bit I2C GPIO expander with input pull-ups",
    "SOIC-16W 1.27 mm",
    "Texas Instruments",
    "TCA9554DWR",
    (10.3, 7.5, 2.65),
    "https://www.ti.com/lit/ds/symlink/tca9554.pdf",
)
