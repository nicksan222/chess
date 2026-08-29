"""Raspberry Pi Pico 2 W controller module."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit

PIN_NAMES = {
    "1": "GP0",
    "2": "GP1",
    "3": "GND",
    "4": "GP2",
    "5": "GP3",
    "6": "GP4",
    "7": "GP5",
    "8": "GND",
    "9": "GP6",
    "10": "GP7",
    "11": "GP8",
    "12": "GP9",
    "13": "GND",
    "14": "GP10",
    "15": "GP11",
    "16": "GP12",
    "17": "GP13",
    "18": "GND",
    "19": "GP14",
    "20": "GP15",
    "21": "GP16",
    "22": "GP17",
    "23": "GND",
    "24": "GP18",
    "25": "GP19",
    "26": "GP20",
    "27": "GP21",
    "28": "GND",
    "29": "GP22",
    "30": "RUN",
    "31": "GP26",
    "32": "GP27",
    "33": "GND",
    "34": "GP28",
    "35": "ADC_VREF",
    "36": "3V3",
    "37": "3V3_EN",
    "38": "GND",
    "39": "VSYS",
    "40": "VBUS",
}


def _build() -> elm.Ic:
    left = [
        elm.IcPin(name=PIN_NAMES[str(n)], pin=str(n), side="left", anchorname=str(n))
        for n in range(1, 21)
    ]
    right = [
        elm.IcPin(name=PIN_NAMES[str(n)], pin=str(n), side="right", anchorname=str(n))
        for n in range(40, 20, -1)
    ]
    # Every pin carries a stub plus a flag, ground or no-connect marker, so the
    # rows need more clearance than the symbol body alone would suggest.
    return integrated_circuit(left + right, "Raspberry Pi Pico 2 W", pinspacing=1.9)


PICO_2_W = Component(
    lib="PICO_2_W",
    value="Pico 2 W",
    description="RP2350 Wi-Fi controller module",
    package="Raspberry Pi Pico",
    build=_build,
    pins=BY_PIN_NUMBER,
)
