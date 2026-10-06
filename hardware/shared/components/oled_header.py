"""Approved product: the board end of the OLED wire harness."""

from .spec import part

# JST SH (1.0 mm) SM04B-SRSS-TB: side-entry SMD header, 2.9 + 0.05 mm high,
# 1.0 A per contact (AWG #28), mates SHR-04V-S-B.
OLED_HEADER = part(
    "OLED_HEADER",
    "4-pin 1.0 mm side-entry header for the OLED harness",
    "SH 4P side entry SMD",
    "JST",
    "SM04B-SRSS-TB",
    (6.0, 4.95, 2.95),
    "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
)
