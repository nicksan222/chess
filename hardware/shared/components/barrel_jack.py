"""Approved product: the rear-panel DC input jack (wired to J4, not on the PCB)."""

from .spec import part

# Switchcraft 722A, drawing "712A 722A 732A" rev J (06-11-21) and the 712A/722A
BARREL_JACK = part(
    "BARREL_JACK",
    "Panel-mount 5.5 x 2.1 mm DC jack, split Ø2.0 centre pin, 5 A, solder lugs",
    "panel mount 5/16-32 bushing",
    "Switchcraft",
    "722A",
    (15.4, 11.0, 11.0),
    "5.5x2.0 mm centre-positive DC jack, 2.5 A rated",
    "5.5x2.0 mm THT",
    "Same Sky",
    "PJ-102A",
    (14.4, 11.0, 11.0),
    "https://www.sameskydevices.com/product/resource/pj-102a.pdf",
)
