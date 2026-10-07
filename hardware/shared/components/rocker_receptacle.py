"""Approved product: the insulated receptacle for each rocker-switch tab."""

from .spec import part

ROCKER_RECEPTACLE = part(
    "ROCKER_RECEPTACLE",
    "FASTON .187 insulated receptacle, 22-18 AWG",
    "FASTON 187 receptacle",
    "TE Connectivity",
    "2-520275-2",
    datasheet="https://media.distrelec.com/Web/Downloads/_t/ds/2-520275-2_eng_tds.pdf",
)

ROCKER_RECEPTACLE_WIRE_GAUGE_AWG = (22, 18)
