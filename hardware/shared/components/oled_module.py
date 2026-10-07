"""2.42-inch white I2C SSD1309 OLED, assembled without its upright header.

MC242GW supplier drawing V1.0 (2023-08-11): 72 x 43 mm PCB,
2.2 mm underside SMD, 1.2 mm PCB and 2.85 mm display frame.
Solder the four harness wires directly to GND/VCC/SCL/SDA pads.
The optional RES pin is left open; the module supplies power-on reset.
"""

from .spec import part

OLED_MODULE = part(
    "OLED_MODULE",
    "2.42 inch white 128x64 SSD1309 I2C OLED module; header uninstalled",
    "72x43 mm module, direct-solder harness",
    "Qdtech / LCDWIKI",
    "MC242GW",
    (72.0, 43.0, 6.25),
    "https://www.lcdwiki.com/res/MC242GX/MC242GX_Specification_EN_V1.0.pdf",
)

OLED_WIDTH_PIXELS = 128
OLED_HEIGHT_PIXELS = 64
OLED_CONTROLLER = "ssd1309"
OLED_REFERENCE_DOCUMENTS = (
    "https://www.lcdwiki.com/res/MC242GX/2.42inch_IIC_Module_MC242GX_Schematic.pdf",
    "https://www.lcdwiki.com/res/MC242GX/2.42inch_SSD1309_Init.txt",
)
OLED_TERMINAL_LABELS = ("GND", "VCC", "SCL", "SDA")

# Intrinsic MC242GW geometry from supplier drawing V1.0. Assembly placement,
# print clearances, ledges and fasteners remain in shared.dimensions.panel.
OLED_SCREEN_SIZE_MM = (55.01, 27.49)
OLED_SCREEN_OFFSET_MM = (0.005, 2.685)
OLED_MOUNT_HOLES_MM = (
    (-34.0, 19.5),
    (34.0, 19.5),
    (-34.0, -19.1),
    (34.0, -19.1),
)
OLED_MOUNT_HOLE_DIAMETER_MM = 3.0
OLED_UNDERSIDE_SIZE_MM = (60.0, 35.0, 2.2)
OLED_PAD_POSITIONS_MM = (
    (-33.5, -3.81),
    (-33.5, -1.27),
    (-33.5, 1.27),
    (-33.5, 3.81),
    (-33.5, 6.35),
)
OLED_PCB_THICKNESS_MM = 1.2
OLED_FRAME_MM = (62.1, 38.8, 2.85)

# R2/R3 in the approved module schematic, each to the 3.3 V logic rail.
OLED_I2C_PULLUP_OHMS = 4_700.0
