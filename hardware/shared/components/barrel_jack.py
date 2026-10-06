"""Approved product: the rear-panel DC input jack (wired to J4, not on the PCB)."""

from .spec import part

BARREL_JACK = part(
    "BARREL_JACK",
    "5.5x2.0 mm centre-positive DC jack, 2.5 A rated",
    "5.5x2.0 mm THT",
    "Same Sky",
    "PJ-102A",
    (14.4, 11.0, 11.0),
    "https://www.sameskydevices.com/product/resource/pj-102a.pdf",
)
