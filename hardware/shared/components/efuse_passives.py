"""Approved products: resistors and capacitors around the U74 eFuse.

Yageo RC thick film (1 %) and RT thin film (RT series V.17, 2026-02-12: B = 0.1 %,
D = 25 ppm/C, RT0603 1 Ohm-1 MOhm in E-24/E-96) 0603 resistors; Yageo CC X7R 0603
capacitors (X7R V.18, 2017-06-16, Table 3: 1.0 nF and 10 nF at 50 V and 1.0 uF
at 25 V, thickness class DA). Values follow TI SLVSFC9C sections 7.3.2-7.3.5: RILM 1.65 kOhm
(1.80-2.20 A); OVLO 604k/169k 0.1 % (S4c: trip 5.34-5.66 V, above the supply's +5 %)
with 10 nF on the OVLO pin against microsecond hot-plug spikes; EN 604k/261k from
RUN (5.25 V / 604k < 10 uA reverse pin current with an ideal clamp, SLVSFC9C 8.2);
dVdt 10 nF; ITIMER 1 nF (S6d: breaker blanking 0.46-1.6 ms, so a full-white or
lit-chain overload stays under the fuse's 20 % pulse rule); IN bypass 1 uF; RUN
wetting load 1 kOhm (about 5 mA).
"""

from .spec import ComponentSpec, part

_RESISTOR_BODY = (1.6, 0.8, 0.55)
_CAPACITOR_BODY = (1.6, 0.8, 0.8)


def _resistor(key: str, ohms: str, mpn: str, film: str) -> ComponentSpec:
    """Define a 0603 Yageo resistor of `ohms` (display text), `film` type and `mpn`, sharing the common body size."""
    return part(
        key,
        f"{ohms} 0.1 W {film} resistor",
        "0603 (1608 metric)",
        "Yageo",
        mpn,
        _RESISTOR_BODY,
        datasheet=(
            "https://www.yageogroup.com/content/datasheet/asset/file/"
            + (
                "PYU-RT_1-TO-0-01_ROHS_L"
                if film == "thin-film"
                else "PYU-RC_GROUP_51_ROHS_L"
            )
        ),
    )


RES_1K65 = _resistor("RES_1K65", "1.65 kohm 1 %", "RC0603FR-071K65L", "thick-film")
RES_1K = _resistor("RES_1K", "1 kohm 1 %", "RC0603FR-071KL", "thick-film")
RES_261K = _resistor("RES_261K", "261 kohm 1 %", "RC0603FR-07261KL", "thick-film")
# S6 LED switch gate drive (interface H5): 10k pull-up, 100k pull-down/gate.
RES_10K = _resistor("RES_10K", "10 kohm 1 %", "RC0603FR-0710KL", "thick-film")
RES_100K = _resistor("RES_100K", "100 kohm 1 %", "RC0603FR-07100KL", "thick-film")
RES_604K_PRECISION = _resistor(
    "RES_604K_PRECISION", "604 kohm 0.1 % 25 ppm", "RT0603BRD07604KL", "thin-film"
)
RES_169K_PRECISION = _resistor(
    "RES_169K_PRECISION", "169 kohm 0.1 % 25 ppm", "RT0603BRD07169KL", "thin-film"
)
CAP_10N = part(
    "CAP_10N",
    "10 nF 50 V X7R MLCC",
    "0603 (1608 metric)",
    "Yageo",
    "CC0603KRX7R9BB103",
    _CAPACITOR_BODY,
    datasheet="https://www.yageogroup.com/download/specsheet/CC0603KRX7R9BB103",
)
CAP_1N = part(
    "CAP_1N",
    "1 nF 50 V X7R MLCC",
    "0603 (1608 metric)",
    "Yageo",
    "CC0603KRX7R9BB102",
    _CAPACITOR_BODY,
    datasheet="https://www.yageogroup.com/download/specsheet/CC0603KRX7R9BB102",
)
CAP_1U = part(
    "CAP_1U",
    "1 uF 25 V X7R MLCC",
    "0603 (1608 metric)",
    "Yageo",
    "CC0603KRX7R8BB105",
    _CAPACITOR_BODY,
    datasheet="https://www.yageogroup.com/download/specsheet/CC0603KRX7R8BB105",
)
