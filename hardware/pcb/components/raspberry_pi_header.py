"""Raspberry Pi 40-pin GPIO header pins used by this board."""

from enum import StrEnum

from base.component import BoardComponent, ComponentReference


class RaspberryPiHeaderPin(StrEnum):
    THREE_VOLTS_THREE = "1"
    FIVE_VOLTS = "2"
    I2C_SDA = "3"
    FIVE_VOLTS_ALT = "4"
    I2C_SCL = "5"
    GROUND_6 = "6"
    SENSE_IRQ_GPIO4 = "7"
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


class RaspberryPiHeader(BoardComponent[RaspberryPiHeaderPin]):
    pin_type = RaspberryPiHeaderPin


HOST_GPIO_HEADER = RaspberryPiHeader(ComponentReference.HOST_GPIO_HEADER)
