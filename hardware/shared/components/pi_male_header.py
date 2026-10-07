"""Approved product: the male header soldered to the Raspberry Pi Zero 2 W."""

from .spec import part

# Sullins .100 in male header catalogue p108, code AA: post .230 [5.84], tail
# .120 [3.05], insulator .100 [2.54]. The SC0510 host ships without this header.
PI_MALE_HEADER = part(
    "PI_MALE_HEADER",
    "2x20 2.54 mm male header for the Pi (insulator 2.54 mm, post 5.84 mm)",
    "2x20 2.54 mm THT",
    "Sullins Connector Solutions",
    "PRPC020DAAN-RC",
    (50.8, 5.08, 2.54),
    "https://www.sullinscorp.com/catalogs/77_PAGE108-109_.100_MALE_HDR.pdf",
)
