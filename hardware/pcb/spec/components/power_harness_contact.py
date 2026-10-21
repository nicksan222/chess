"""Approved product: the crimp contact used by the power harness."""

from .spec import part

POWER_HARNESS_CONTACT = part(
    "POWER_HARNESS_CONTACT",
    "VH crimp contact, AWG 22-18, insulation 1.7-3.0 mm",
    "VH crimp contact",
    "JST",
    "SVH-21T-P1.1",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eVH.pdf",
)

POWER_HARNESS_WIRE_GAUGE_AWG = (22, 18)
