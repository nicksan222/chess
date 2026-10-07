"""Approved product: AZ-Delivery 0.96 in SSD1306 I2C OLED module.

Off-board: connected through header J2 and listed in the human BOM only. The
module's pin order is not asserted. The linked vendor document lists a
28x33 mm module while this catalog records 27x27 mm; the revision and fit
need reconciliation before changing the authoritative geometry.
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
    "https://cdn.shopify.com/s/files/1/1509/1638/files/0_96_Zoll_Display_Datenblatt_AZ-Delivery_Vertriebs_GmbH_241c4223-c03f-4530-a8c0-f9ef2575872f.pdf?v=1622442722",
)
