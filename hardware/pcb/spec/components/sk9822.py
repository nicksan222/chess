"""Approved product: SK9822 5050 RGB LED (one per square, daisy-chained)."""

from .spec import part

# Opsco SK9822-A (SPC/SK9822-A Rev 01, the orderable code; manufacturing review,
# lead decision S4c): 5050 top-SMD, 5.0 mm body, 5.4 mm over leads, 1.6 mm high
# (p3 §4, +-0.1 mm).
SK9822 = part(
    "SK9822",
    "Clocked 5050 RGB LED",
    "PLCC-6 5050",
    "Opsco Optoelectronics",
    "SK9822-A",
    (5.4, 5.0, 1.6),
    "https://www.rose-lighting.com/wp-content/uploads/sites/53/2020/05/"
    "SK9822-A-REV.01-EN-5050-RGB-27K-HZ-PWM-30M-bps-speed.pdf",
)
