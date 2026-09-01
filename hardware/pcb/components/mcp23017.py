"""MCP23017 GPIO expander pins."""

from enum import StrEnum
from .base import BoardComponent


class Mcp23017Pin(StrEnum):
    """SPDIP pinout from Microchip data sheet DS20001952D, table 2-1."""

    GPIO_B0 = "1"
    GPIO_B1 = "2"
    GPIO_B2 = "3"
    GPIO_B3 = "4"
    GPIO_B4 = "5"
    GPIO_B5 = "6"
    GPIO_B6 = "7"
    GPIO_B7 = "8"
    SUPPLY = "9"
    GROUND = "10"
    NOT_CONNECTED_11 = "11"
    I2C_CLOCK = "12"
    I2C_DATA = "13"
    NOT_CONNECTED_14 = "14"
    ADDRESS_0 = "15"
    ADDRESS_1 = "16"
    ADDRESS_2 = "17"
    ACTIVE_LOW_RESET = "18"
    INTERRUPT_B = "19"
    INTERRUPT_A = "20"
    GPIO_A0 = "21"
    GPIO_A1 = "22"
    GPIO_A2 = "23"
    GPIO_A3 = "24"
    GPIO_A4 = "25"
    GPIO_A5 = "26"
    GPIO_A6 = "27"
    GPIO_A7 = "28"


class Mcp23017(BoardComponent[Mcp23017Pin]):
    pin_type = Mcp23017Pin
