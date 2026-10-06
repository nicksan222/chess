"""Approved product: bulk LED-rail capacitor (two fitted, bottom side)."""

from .spec import part

# Rubycon ZLJ catalogue p81/p2: 10 V 560 uF 8x11.5, 1200 mA ripple, 0.075 Ohm
# (20 °C, 100 kHz); envelope φD + 0.5 by L + α (α = 1.5) = 8.5 x 13.0.
CAP_560U = part(
    "CAP_560U",
    "560 uF 10 V low-ESR electrolytic",
    "radial 8 mm",
    "Rubycon",
    "10ZLJ560M8X11.5",
    (8.5, 8.5, 13.0),
    "https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/ZLJ.pdf",
)
