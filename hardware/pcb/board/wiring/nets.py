"""Typed names for reviewed global nets.

Anonymous LED-chain nets intentionally remain generated names because their
identity is positional rather than semantic.
"""

from enum import StrEnum


class Net(StrEnum):
    GROUND = "GND"
    FIVE_VOLTS = "+5V"
    THREE_VOLTS_THREE = "+3V3"
    DC_INPUT = "DC_IN"
    DC_FUSED = "DC_FUSED"
    I2C_SDA = "I2C_SDA"
    I2C_SCL = "I2C_SCL"
    SENSE_IRQ = "SENSE_IRQ"
    SPI_CLOCK = "SPI_CLK_3V3"
    SPI_DATA = "SPI_DATA_3V3"
    LED_CLOCK = "LED_CLK_5V"
    LED_DATA = "LED_DATA_5V"


class ButtonNet(StrEnum):
    UP = "BTN_UP"
    DOWN = "BTN_DOWN"
    LEFT = "BTN_LEFT"
    RIGHT = "BTN_RIGHT"
    OK = "BTN_OK"
    RESET = "BTN_RESET"
    PASS = "BTN_PASS"
    F1 = "BTN_F1"
    F2 = "BTN_F2"
    F3 = "BTN_F3"
    F4 = "BTN_F4"
    F5 = "BTN_F5"
