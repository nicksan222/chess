"""Approved product: TI TPS259474ARPW eFuse (input protection, U74).

TI SLVSFC9C (Oct 2020, rev May 2026): 2.7-23 V, IN withstands -15 V, back-to-back
FETs (true reverse-current blocking), RON 28.2 mOhm typ / 45 mOhm max, adjustable
OVLO and EN/UVLO (1.183-1.223 V), circuit breaker with auto-retry (474A), dVdt
inrush control. RPW0010A VQFN-HR: body 1.9-2.1 mm square, 1 mm max height.
"""

from .spec import part

EFUSE = part(
    "EFUSE",
    "2.7-23 V 5.5 A eFuse, reverse polarity, OVLO, circuit breaker",
    "VQFN-HR-10 RPW 2x2 mm",
    "Texas Instruments",
    # Orderable code: tape and reel of the same die/package (TI part details), MSL 2.
    "TPS259474ARPWR",
    (2.0, 2.0, 1.0),
    "https://www.ti.com/lit/ds/symlink/tps25947.pdf",
)
