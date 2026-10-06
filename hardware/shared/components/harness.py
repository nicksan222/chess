"""Off-board harness and Pi-header parts: bought and assembled, not on the PCB."""

from .spec import ComponentSpec, part

# Sullins .100 in male header catalogue p108, code AA: post .230 [5.84], tail .120
# [3.05], insulator .100 [2.54]; soldered to the Pi Zero 2 W (SC0510 ships bare).
PI_MALE_HEADER = part(
    "PI_MALE_HEADER",
    "2x20 2.54 mm male header for the Pi (insulator 2.54 mm, post 5.84 mm)",
    "2x20 2.54 mm THT",
    "Sullins Connector Solutions",
    "PRPC020DAAN-RC",
    (50.8, 5.08, 2.54),
    "https://www.sullinscorp.com/catalogs/77_PAGE108-109_.100_MALE_HDR.pdf",
)
# JST VH catalogue p2: receptacle housing and AWG #22-#18 crimp contact for J4.
POWER_HARNESS_HOUSING = part(
    "POWER_HARNESS_HOUSING",
    "4-pin VH receptacle housing for the power harness",
    "VH 4P housing",
    "JST",
    "VHR-4N",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eVH.pdf",
)
POWER_HARNESS_CONTACT = part(
    "POWER_HARNESS_CONTACT",
    "VH crimp contact, AWG 22-18, insulation 1.7-3.0 mm",
    "VH crimp contact",
    "JST",
    "SVH-21T-P1.1",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eVH.pdf",
)
# TE FASTON .187 insulated receptacle, 22-18 AWG, for the rocker's 4.75 mm tabs.
ROCKER_RECEPTACLE = part(
    "ROCKER_RECEPTACLE",
    "FASTON .187 insulated receptacle, 22-18 AWG",
    "FASTON 187 receptacle",
    "TE Connectivity",
    "2-520275-2",
    datasheet="https://media.distrelec.com/Web/Downloads/_t/ds/2-520275-2_eng_tds.pdf",
)
# JST SH catalogue p1/p4: housing and AWG #32-#28 crimp contact for J2.
OLED_HARNESS_HOUSING = part(
    "OLED_HARNESS_HOUSING",
    "4-pin SH receptacle housing for the OLED harness",
    "SH 4P housing",
    "JST",
    "SHR-04V-S-B",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
)
OLED_HARNESS_CONTACT = part(
    "OLED_HARNESS_CONTACT",
    "SH crimp contact, AWG 32-28, insulation 0.4-0.8 mm",
    "SH crimp contact",
    "JST",
    "SSH-003T-P0.2-H",
    datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
)


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
POWER_WIRE_LENGTH_MM = 200.0
OLED_WIRE_LENGTH_MM = 90.0


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
