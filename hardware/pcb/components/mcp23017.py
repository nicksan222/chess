"""MCP23017 GPIO expander pins."""

from enum import StrEnum
from .base import BoardComponent


class Mcp23017Pin(StrEnum):
    GPIO_A0 = "1"
    GPIO_A1 = "2"
    GPIO_A2 = "3"
    GPIO_A3 = "4"
    GPIO_A4 = "5"
    GPIO_A5 = "6"
    GPIO_A6 = "7"
    GPIO_A7 = "8"
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
    INTERRUPT_A = "19"
    INTERRUPT_B = "20"
    GPIO_B0 = "21"
    GPIO_B1 = "22"
    GPIO_B2 = "23"
    GPIO_B3 = "24"
    GPIO_B4 = "25"
    GPIO_B5 = "26"
    GPIO_B6 = "27"
    GPIO_B7 = "28"


class Mcp23017(BoardComponent[Mcp23017Pin]):
    pin_type = Mcp23017Pin
