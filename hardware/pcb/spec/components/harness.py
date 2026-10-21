"""Colour-specific wire products and cut lengths for the off-board harnesses."""

from .spec import ComponentSpec, part

# Alpha Wire colour suffixes (BK black, RD red, OR orange, WH white, YL yellow,
# BL blue) with put-up 005 (100 ft spool): bought by the spool, one BOM line per
# colour, and each kit takes its cut length (reviewer-s4 m8).
ALPHA_COLOUR_CODES = {
    "black": "BK",
    "red": "RD",
    "orange": "OR",
    "white": "WH",
    "yellow": "YL",
    "blue": "BL",
}
# Alpha 3055 specification: .079 +/- .002 inch OD; use the maximum.
# OLED PTFE uses the contact's conservative .8 mm insulation limit.
WIRE_OUTSIDE_DIAMETERS_MM = {18: 0.081 * 25.4, 28: 0.8}
POWER_WIRE_LENGTH_MM = 200.0
# Center-mounted external display: ~112 mm connector-to-module span plus
# dressing and service slack. The four conductors retain their identities.
OLED_WIRE_LENGTH_MM = 180.0


def _alpha_wire(
    key: str, series: str, kind: str, colour: str, length_mm: float
) -> ComponentSpec:
    """Define one colour of an Alpha Wire spool: key suffixed with the colour, and the MPN built from the series and the colour code."""
    return part(
        f"{key}_{colour.upper()}",
        f"{kind}, {colour}",
        kind,
        "Alpha Wire",
        f"{series} {ALPHA_COLOUR_CODES[colour]}005",
        datasheet=(
            "https://www.alphawire.com/disteAPI/SpecPDF/DownloadProductSpecPdf?productPartNumber="
            + series.replace("/", "%2F")
        ),
        purchase_unit="100 ft spool",
        cut_length_mm=length_mm,
    )


# 18 AWG stranded UL1007 (Alpha 3055 series); JST rates the VH contact 7 A with
# AWG #18. Four colours so a cavity 1 <-> 4 swap is visible (reviewer-s3c M-a).
POWER_HARNESS_WIRES = {
    colour: _alpha_wire(
        "POWER_HARNESS_WIRE", "3055", "18 AWG UL1007 wire", colour, POWER_WIRE_LENGTH_MM
    )
    for colour in ("red", "black", "orange", "white")
}
# 28 AWG 7/36 PTFE (Alpha 2842/7, MIL-W-16878 type ET), OD 0.027 in (0.69 mm):
# inside the SSH contact's 0.4-0.8 mm insulation range (UL1007 28 AWG, 1.19 mm,
# is not).
OLED_HARNESS_WIRES = {
    colour: _alpha_wire(
        "OLED_HARNESS_WIRE", "2842/7", "28 AWG PTFE wire", colour, OLED_WIRE_LENGTH_MM
    )
    for colour in ("black", "red", "yellow", "blue")
}
