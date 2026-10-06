"""Approved product: the rear-panel DC input jack (wired to J4, not on the PCB)."""

from .spec import part

# Switchcraft 722A, drawing "712A 722A 732A" rev J (06-11-21) and the 712A/722A
# sheet: split centre pin Ø0.080 in (2.0 mm) for the 5.5 x 2.1 plug system,
# 5 A 12 V DC, 0.01 ohm max contact (initial); 5/16-32 NEF bushing 0.215 in
# (5.46), panel <= .125 in, Ø0.43 in (11.0) flange; 0.82 - 0.215 in (15.4 mm)
# behind the flange to the lug ends. Lugs: CENTER PIN, SLEEVE, SLEEVE SHUNT.
BARREL_JACK = part(
    "BARREL_JACK",
    "Panel-mount 5.5 x 2.1 mm DC jack, split Ø2.0 centre pin, 5 A, solder lugs",
    "panel mount 5/16-32 bushing",
    "Switchcraft",
    "722A",
    (15.4, 11.0, 11.0),
    "https://www.switchcraft.com/assets/1/24/712A%20722A%20732A_CD.PDF",
)
