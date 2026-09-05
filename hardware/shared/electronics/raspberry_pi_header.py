"""Typed Raspberry Pi 40-pin header and its human-readable board legend."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.components import PI_ZERO_HEADER
from shared.electronics.base import ElectronicComponent


class RaspberryPiHeaderPin(StrEnum):
    THREE_VOLTS_THREE = "1"
    FIVE_VOLTS = "2"
    I2C_SDA = "3"
    FIVE_VOLTS_ALT = "4"
    I2C_SCL = "5"
    GROUND_6 = "6"
    GPIO4 = "7"
    UART_TX_GPIO14 = "8"
    GROUND_9 = "9"
    UART_RX_GPIO15 = "10"
    BUTTON_RESET_GPIO17 = "11"
    GPIO18 = "12"
    GPIO27 = "13"
    GROUND_14 = "14"
    BUTTON_F3_GPIO22 = "15"
    BUTTON_F4_GPIO23 = "16"
    THREE_VOLTS_THREE_ALT = "17"
    BUTTON_F5_GPIO24 = "18"
    SPI_DATA_GPIO10 = "19"
    GROUND_20 = "20"
    SPI_MISO_GPIO9 = "21"
    GPIO25 = "22"
    SPI_CLOCK_GPIO11 = "23"
    SPI_CE0_GPIO8 = "24"
    GROUND_25 = "25"
    SPI_CE1_GPIO7 = "26"
    ID_EEPROM_DATA = "27"
    ID_EEPROM_CLOCK = "28"
    BUTTON_UP_GPIO5 = "29"
    GROUND_30 = "30"
    BUTTON_DOWN_GPIO6 = "31"
    BUTTON_LEFT_GPIO12 = "32"
    BUTTON_RIGHT_GPIO13 = "33"
    GROUND_34 = "34"
    BUTTON_PASS_GPIO19 = "35"
    BUTTON_OK_GPIO16 = "36"
    GPIO26 = "37"
    BUTTON_F1_GPIO20 = "38"
    GROUND_39 = "39"
    BUTTON_F2_GPIO21 = "40"


class HeaderLegend(StrEnum):
    SDA = "SDA"
    SCL = "SCL"
    RESET = "RESET"
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"
    SPI_DATA = "SPI-DATA"
    SPI_CLOCK = "SPI-CLK"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    PASS = "PASS"
    OK = "OK"


@dataclass(frozen=True)
class HeaderLegendEntry:
    """One checked physical pin-to-function label."""

    pin: RaspberryPiHeaderPin
    label: HeaderLegend

    def render(self) -> str:
        return f"{self.pin.value} {self.label.value}"


class RaspberryPiHeaderComponent(ElectronicComponent[RaspberryPiHeaderPin]):
    """Header pinout plus the board-facing legend derived from those pins."""

    pin_type = RaspberryPiHeaderPin
    specs = (PI_ZERO_HEADER,)

    _FUNCTION_ROWS = (
        (
            HeaderLegendEntry(RaspberryPiHeaderPin.I2C_SDA, HeaderLegend.SDA),
            HeaderLegendEntry(RaspberryPiHeaderPin.I2C_SCL, HeaderLegend.SCL),
            HeaderLegendEntry(
                RaspberryPiHeaderPin.BUTTON_RESET_GPIO17, HeaderLegend.RESET
            ),
            HeaderLegendEntry(RaspberryPiHeaderPin.BUTTON_F3_GPIO22, HeaderLegend.F3),
        ),
        (
            HeaderLegendEntry(RaspberryPiHeaderPin.BUTTON_F4_GPIO23, HeaderLegend.F4),
            HeaderLegendEntry(RaspberryPiHeaderPin.BUTTON_F5_GPIO24, HeaderLegend.F5),
            HeaderLegendEntry(
                RaspberryPiHeaderPin.SPI_DATA_GPIO10, HeaderLegend.SPI_DATA
            ),
            HeaderLegendEntry(
                RaspberryPiHeaderPin.SPI_CLOCK_GPIO11, HeaderLegend.SPI_CLOCK
            ),
        ),
        (
            HeaderLegendEntry(RaspberryPiHeaderPin.BUTTON_UP_GPIO5, HeaderLegend.UP),
            HeaderLegendEntry(
                RaspberryPiHeaderPin.BUTTON_DOWN_GPIO6, HeaderLegend.DOWN
            ),
            HeaderLegendEntry(
                RaspberryPiHeaderPin.BUTTON_LEFT_GPIO12, HeaderLegend.LEFT
            ),
            HeaderLegendEntry(
                RaspberryPiHeaderPin.BUTTON_RIGHT_GPIO13, HeaderLegend.RIGHT
            ),
            HeaderLegendEntry(
                RaspberryPiHeaderPin.BUTTON_PASS_GPIO19, HeaderLegend.PASS
            ),
            HeaderLegendEntry(RaspberryPiHeaderPin.BUTTON_OK_GPIO16, HeaderLegend.OK),
        ),
    )
    _GROUND_PINS = (
        RaspberryPiHeaderPin.GROUND_6,
        RaspberryPiHeaderPin.GROUND_9,
        RaspberryPiHeaderPin.GROUND_14,
        RaspberryPiHeaderPin.GROUND_20,
        RaspberryPiHeaderPin.GROUND_25,
        RaspberryPiHeaderPin.GROUND_30,
        RaspberryPiHeaderPin.GROUND_34,
        RaspberryPiHeaderPin.GROUND_39,
    )

    @classmethod
    def silkscreen_pinout_lines(cls) -> tuple[str, str, str, str]:
        """Render the compact four-line legend from typed pin roles."""
        function_rows = tuple(
            "  ".join(entry.render() for entry in row) for row in cls._FUNCTION_ROWS
        )
        final_functions = "  ".join(
            entry.render()
            for entry in (
                HeaderLegendEntry(
                    RaspberryPiHeaderPin.BUTTON_F1_GPIO20, HeaderLegend.F1
                ),
                HeaderLegendEntry(
                    RaspberryPiHeaderPin.BUTTON_F2_GPIO21, HeaderLegend.F2
                ),
            )
        )
        three_volts = "/".join(
            pin.value
            for pin in (
                RaspberryPiHeaderPin.THREE_VOLTS_THREE,
                RaspberryPiHeaderPin.THREE_VOLTS_THREE_ALT,
            )
        )
        five_volts = "/".join(
            pin.value
            for pin in (
                RaspberryPiHeaderPin.FIVE_VOLTS,
                RaspberryPiHeaderPin.FIVE_VOLTS_ALT,
            )
        )
        grounds = "/".join(pin.value for pin in cls._GROUND_PINS)
        return (
            f"J1 PI: {function_rows[0]}",
            function_rows[1],
            function_rows[2],
            f"{final_functions} | {three_volts} 3V3 | {five_volts} 5V | GND: {grounds}",
        )
