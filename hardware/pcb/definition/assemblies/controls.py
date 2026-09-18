"""Host GPIO, level shifting, display, and twelve direct panel buttons."""

from __future__ import annotations

import pcbnew

from pcb.definition.assemblies.power import add_strip
from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts import catalog as parts
from shared import dimensions, wiring
from shared import electronics as p
from shared.panel import PANEL_BUTTONS


def add_controls(board: pcbnew.BOARD) -> None:
    host = place(
        board,
        parts.PI_ZERO_HEADER_PART,
        "J1",
        at=dimensions.PI_BAY_CENTER_MM,
        rotation=dimensions.PI_HEADER_ROTATION_DEG,
        assembly="controls",
    )
    display = add_strip(
        board,
        parts.OLED_HEADER_PART,
        "J2",
        assembly="controls",
    )
    buffer = add_strip(
        board,
        parts.AHCT125_PART,
        "U5",
        assembly="controls",
    )
    bypass = add_strip(
        board,
        parts.CAP_100N_PART,
        "C7",
        assembly="controls",
        purpose="Buffer decoupling capacitor",
    )
    sda_pullup = add_strip(
        board,
        parts.RES_4K7_PART,
        "R1",
        assembly="controls",
        purpose="I2C pull-up",
    )
    scl_pullup = add_strip(
        board,
        parts.RES_4K7_PART,
        "R2",
        assembly="controls",
        purpose="I2C pull-up",
    )
    connect(
        board,
        "+5V",
        host.pin(p.RaspberryPiHeaderPin.FIVE_VOLTS),
        host.pin(p.RaspberryPiHeaderPin.FIVE_VOLTS_ALT),
        buffer.pin(p.Ahct125Pin.SUPPLY),
        buffer.pin(p.Ahct125Pin.BUFFER_3_OUTPUT_ENABLE),
        buffer.pin(p.Ahct125Pin.BUFFER_4_OUTPUT_ENABLE),
        bypass.pin(p.CapacitorPin.SUPPLY_OR_ELECTRODE_A),
    )
    connect(
        board,
        "+3V3",
        host.pin(p.RaspberryPiHeaderPin.THREE_VOLTS_THREE),
        host.pin(p.RaspberryPiHeaderPin.THREE_VOLTS_THREE_ALT),
        display.pin(p.OledHeaderPin.THREE_VOLTS_THREE),
        sda_pullup.pin(p.ResistorPin.TERMINAL_A),
        scl_pullup.pin(p.ResistorPin.TERMINAL_A),
    )
    connect(
        board,
        "GND",
        *(
            host.pin(pin)
            for pin in p.RaspberryPiHeaderPin
            if pin.name.startswith("GROUND_")
        ),
        display.pin(p.OledHeaderPin.GROUND),
        buffer.pin(p.Ahct125Pin.GROUND),
        bypass.pin(p.CapacitorPin.RETURN_OR_ELECTRODE_B),
        *(
            buffer.pin(pin)
            for pin in (
                p.Ahct125Pin.BUFFER_1_OUTPUT_ENABLE,
                p.Ahct125Pin.BUFFER_2_OUTPUT_ENABLE,
                p.Ahct125Pin.BUFFER_3_INPUT,
                p.Ahct125Pin.BUFFER_4_INPUT,
            )
        ),
    )
    connect(
        board,
        wiring.SDA_NET,
        host.pin(p.RaspberryPiHeaderPin.I2C_SDA),
        display.pin(p.OledHeaderPin.I2C_DATA),
        sda_pullup.pin(p.ResistorPin.TERMINAL_B),
    )
    connect(
        board,
        wiring.SCL_NET,
        host.pin(p.RaspberryPiHeaderPin.I2C_SCL),
        display.pin(p.OledHeaderPin.I2C_CLOCK),
        scl_pullup.pin(p.ResistorPin.TERMINAL_B),
    )
    connect(
        board,
        wiring.SPI_DATA_NET,
        host.pin(p.RaspberryPiHeaderPin.SPI_DATA_GPIO10),
        buffer.pin(p.Ahct125Pin.BUFFER_1_INPUT),
    )
    connect(
        board,
        wiring.SPI_CLOCK_NET,
        host.pin(p.RaspberryPiHeaderPin.SPI_CLOCK_GPIO11),
        buffer.pin(p.Ahct125Pin.BUFFER_2_INPUT),
    )
    connect(board, wiring.LED_DATA_NET, buffer.pin(p.Ahct125Pin.BUFFER_1_OUTPUT))
    connect(board, wiring.LED_CLOCK_NET, buffer.pin(p.Ahct125Pin.BUFFER_2_OUTPUT))
    for pin in (p.Ahct125Pin.BUFFER_3_OUTPUT, p.Ahct125Pin.BUFFER_4_OUTPUT):
        no_connect(board, buffer.pin(pin))
    # Explicit unused host pins; omission is never interpreted as no-connect.
    for pin in (
        p.RaspberryPiHeaderPin.GPIO4,
        p.RaspberryPiHeaderPin.UART_TX_GPIO14,
        p.RaspberryPiHeaderPin.UART_RX_GPIO15,
        p.RaspberryPiHeaderPin.GPIO18,
        p.RaspberryPiHeaderPin.GPIO27,
        p.RaspberryPiHeaderPin.SPI_MISO_GPIO9,
        p.RaspberryPiHeaderPin.GPIO25,
        p.RaspberryPiHeaderPin.SPI_CE0_GPIO8,
        p.RaspberryPiHeaderPin.SPI_CE1_GPIO7,
        p.RaspberryPiHeaderPin.ID_EEPROM_DATA,
        p.RaspberryPiHeaderPin.ID_EEPROM_CLOCK,
        p.RaspberryPiHeaderPin.GPIO26,
    ):
        no_connect(board, host.pin(pin))
    # Explicit function order keeps button references stable.
    for button in PANEL_BUTTONS:
        switch = place(
            board,
            parts.BUTTON_PART,
            button.switch_reference,
            at=button.position_mm,
            assembly="controls",
            extras={"Function": button.name},
        )
        pin = p.RaspberryPiHeaderPin[f"BUTTON_{button.name}_GPIO{button.gpio}"]
        connect(
            board,
            button.net_name,
            host.pin(pin),
            switch.pin(p.TactileSwitchPin.SIGNAL),
        )
        connect(board, "GND", switch.pin(p.TactileSwitchPin.GROUND))
    for reference, net, description in (
        ("TP3", wiring.LED_DATA_NET, "Buffered LED data test point"),
        ("TP4", wiring.LED_CLOCK_NET, "Buffered LED clock test point"),
        ("TP6", wiring.SCL_NET, "I2C clock test point"),
        ("TP7", wiring.SDA_NET, "I2C data test point"),
    ):
        probe = add_strip(
            board,
            parts.TEST_POINT_PART,
            reference,
            assembly="controls",
            nominal_value=net,
            purpose=description,
        )
        connect(board, net, probe.pin(p.TestPointPin.PROBE))
