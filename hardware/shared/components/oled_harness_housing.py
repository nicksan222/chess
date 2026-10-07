"""Approved product: the JST SH housing on the off-board OLED harness."""

from .spec import part

OLED_HARNESS_HOUSING = part(
    "OLED_HARNESS_HOUSING",
    "4-pin SH receptacle housing for the OLED harness",
    "SH 4P housing",
    "JST",
    "SHR-04V-S-B",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
)

OLED_HARNESS_CAVITY_NUMBERS = (1, 2, 3, 4)
