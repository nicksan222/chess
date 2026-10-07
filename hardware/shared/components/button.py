"""Approved product: E-Switch TL1105CF100Q panel tactile switch (SW1-SW12)."""

from .spec import part

# E-Switch TL1105 (2.28.2018) pp24-25: "C" actuator = 8.0 mm overall above the PCB,
# Ø3.50 round stem, 3.60 mm body, 6.00 mm square.
BUTTON = part(
    "BUTTON",
    "6 mm tactile switch, Ø3.5 mm round stem, 8.0 mm overall",
    "6x6 mm THT",
    "E-Switch",
    "TL1105CF100Q",
    (6.0, 6.0, 8.0),
    "https://www.e-switch.com/wp-content/uploads/2022/06/TL1105.pdf",
)

# Intrinsic TL1105 "C" geometry from the same catalogue drawing.
BUTTON_HOUSING_MM = (*BUTTON.require_body_mm()[:2], 3.6)
BUTTON_ACTUATOR_DIAMETER_MM = 3.5
