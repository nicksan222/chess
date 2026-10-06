"""Approved product: AZ-Delivery 0.96 in SSD1306 I2C OLED module.

Off-board: connected through header J2 and listed in the human BOM only. The
module's pin order is not asserted: no module datasheet was obtained.
"""

from .spec import part

# AZ-Delivery product-page SKU for the single-module variant.
OLED_MODULE = part(
    "OLED_MODULE",
    "0.96 inch 128x64 SSD1306 four-pin I2C OLED module",
    "27x27 mm module",
    "AZ-Delivery",
    "A 1-9",
    (27.0, 27.0, 4.1),
    "https://www.az-delivery.de/products/0-96zolldisplay",
)
