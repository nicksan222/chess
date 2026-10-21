"""Approved product: the crimp contact used by the OLED harness."""

from .spec import part

OLED_HARNESS_CONTACT = part(
    "OLED_HARNESS_CONTACT",
    "SH crimp contact, AWG 32-28, insulation 0.4-0.8 mm",
    "SH crimp contact",
    "JST",
    "SSH-003T-P0.2-H",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
)

OLED_HARNESS_WIRE_GAUGE_AWG = (32, 28)
