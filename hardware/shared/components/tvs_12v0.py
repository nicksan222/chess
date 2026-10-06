"""Approved product: Littelfuse SMBJ12CA bidirectional TVS on the eFuse input.

User decision D2 (2026-10-06): the U74 OVLO handles any adapter up to about 13 V,
so the TVS only clamps surges. Littelfuse SMBJ (rev 06/03/20) p2 row SMBJ12CA: VR
12.0 V, VBR 13.30-14.70 V at 1 mA, VC 19.9 V at IPP 30.2 A, IR 1 uA. VC stays under
U74 IN's 28 V. Bidirectional, so a reversed plug does not forward-bias it (TI
SLVSFC9C 8.3.1).
"""

from .spec import part

TVS_12V0 = part(
    "TVS_12V0",
    "12 V standoff (13.3 V min breakdown) bidirectional TVS diode",
    "SMB (DO-214AA)",
    "Littelfuse",
    "SMBJ12CA",
    (4.6, 3.6, 2.3),
    "https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-datasheet",
)
