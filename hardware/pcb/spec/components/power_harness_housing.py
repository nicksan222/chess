"""Approved product: the JST VH housing on the off-board power harness."""

from .spec import part

POWER_HARNESS_HOUSING = part(
    "POWER_HARNESS_HOUSING",
    "4-pin VH receptacle housing for the power harness",
    "VH 4P housing",
    "JST",
    "VHR-4N",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eVH.pdf",
)

POWER_HARNESS_CAVITY_NUMBERS = (1, 2, 3, 4)
