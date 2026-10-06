"""Open verification items that must be closed before fabrication is released.

`UNVERIFIED` names approved parts whose land pattern has no cited manufacturer
source. `ASSUMPTIONS` names design values the sources do not give, with the value
used. Both are informational for `review`; `release` refuses while either is
non-empty (`build.verification_gate`, via `build.release_gates`). `tests/board/test_land_patterns.py`
checks that every catalog part is either golden-verified or listed here.
"""

from types import MappingProxyType

from shared.dimensions import UNVERIFIED_DIMENSIONS

UNVERIFIED: MappingProxyType[str, str] = MappingProxyType({})

ASSUMPTIONS = MappingProxyType(
    {
        "PTH copper rings": (
            "0.4 mm annulus (rules.THT_ANNULAR_RING_MM) on JST VH (J4), TL1105, "
            "Sullins and Rubycon pads: their drawings give holes only"
        ),
        "CAP_560U drill": (
            "0.9 mm: Rubycon ZLJ lead φ0.6 plus the repository's 0.3 mm THT "
            "allowance; no recommended hole is published"
        ),
        "OLED harness": (
            "J2 pins are GND/3V3/SCL/SDA and the harness is soldered to the module "
            "by its printed pad labels; the module's 3.3 V behaviour has no "
            "datasheet on file (pull-ups: see OLED pull-ups)"
        ),
        "Jack/plug fit": (
            "Switchcraft 722A split Ø0.080 in centre pin is made for the 5.5 x 2.1 "
            "plug (EDG41 p134: S760, bore 2.03-2.13; plf6: pin .075-.077 in, "
            "insertion <= 3 lb, withdrawal >= 4 oz, contact <= 0.01 ohm initial, "
            "0.02 ohm after humidity and durability); the GST12A05-P1J plug itself "
            "is not dimensioned on file; bench fit/retention/contact check"
        ),
        "J4 back offset": (
            "B4PS-VH body taken to start 1.0 mm behind the hole row; JST VH p3/p4 "
            "do not dimension it"
        ),
        "J2 circuit 1": (
            "SH side-entry land p1 has no circuit-1 mark; pin 1 at -X with the "
            "tabs at -Y is inferred from the p2 top view"
        ),
        "Harness parts": (
            "18 AWG wire (Alpha Wire 3055, four colour suffixes), 28 AWG PTFE wire "
            "(Alpha Wire 2842/7, 0.69 mm OD for the SSH contact, four colours) and "
            "TE 2-520275-2 FASTON (0.81 mm tab) "
            "are from distributor listings; manufacturing confirms the MPNs (the "
            "RA1 tab is 4.80 x 0.80 mm, E-Switch RA1 catalog drawing 11/2/2022, "
            "which the 0.81 mm FASTON fits)"
        ),
        "Pi Wi-Fi": (
            "Pi Zero 2 W PCB antenna (inferred, board x 118..138.5, y -54.5..-48.5) "
            "sits 11 mm under the full-plane 8-layer board in a printed case; no "
            "copper window (the rank-3 LED chain crosses that area); bench: hotspot "
            "RSSI/throughput at 1/3/10 m, case closed vs open"
        ),
    }
)
