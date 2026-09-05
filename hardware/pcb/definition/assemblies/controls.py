"""Host GPIO, level shifting, display, and twelve direct panel buttons."""

from __future__ import annotations

import pcbnew

from pcb.definition.assemblies.power import add_strip
from pcb.definition.native import connect, no_connect, place
from shared import dimensions, wiring
from shared import electronics as p
from shared.electronics import Ahct125Component as Ahct125
from shared.electronics import CapacitorComponent as Capacitor
from shared.electronics import OledHeaderComponent as OledHeader
from shared.electronics import RaspberryPiHeaderComponent as RaspberryPiHeader
from shared.electronics import ResistorComponent as Resistor
from shared.electronics import TactileSwitchComponent as TactileSwitch
from shared.electronics import TestPointComponent as TestPoint


def add_controls(board: pcbnew.BOARD) -> None:
    host = place(
        board,
        RaspberryPiHeader("J1"),
        part_key="PI_ZERO_HEADER",
        at=dimensions.PI_BAY_CENTER_MM,
        rotation=dimensions.PI_HEADER_ROTATION_DEG,
        assembly="controls",
        library="PI_HEADER",
        value="2x20 header",
        description="Raspberry Pi Zero 2 W GPIO socket",
    )
    display = add_strip(
        board,
        OledHeader("J2"),
        part_key="OLED_HEADER",
        assembly="controls",
        library="OLED_HEADER",
        value="1x4 header",
        description="SSD1306 OLED module connector",
    )
    buffer = add_strip(
        board,
        Ahct125("U5"),
        part_key="AHCT125",
        assembly="controls",
        library="AHCT125",
        value="SN74AHCT125DR",
        description="Quad 5 V buffer accepts 3.3 V SPI clock and data",
    )
    bypass = add_strip(
        board,
        Capacitor("C7"),
        part_key="CAP_100N",
        assembly="controls",
        library="C",
        value="100nF",
        description="Buffer decoupling capacitor",
    )
    sda_pullup = add_strip(
        board,
        Resistor("R1"),
        part_key="RES_4K7",
        assembly="controls",
        library="R",
        value="4.7k",
        description="I2C pull-up",
    )
    scl_pullup = add_strip(
        board,
        Resistor("R2"),
        part_key="RES_4K7",
        assembly="controls",
        library="R",
        value="4.7k",
        description="I2C pull-up",
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
    buttons = (
        "UP",
        "DOWN",
        "LEFT",
        "RIGHT",
        "OK",
        "RESET",
        "PASS",
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
    )
    positions = dict(
        zip(wiring.BUTTON_NAMES, dimensions.PANEL_BUTTON_POSITIONS_MM, strict=True)
    )
    for index, name in enumerate(buttons, 1):
        switch = place(
            board,
            TactileSwitch(f"SW{index}"),
            part_key="BUTTON",
            at=positions[name],
            assembly="controls",
            library="BUTTON",
            value="TACT 6mm",
            description="Momentary panel button, 9.5 mm actuator",
            extras={"Function": name},
        )
        pin = p.RaspberryPiHeaderPin[f"BUTTON_{name}_GPIO{wiring.BUTTON_GPIO[name]}"]
        connect(
            board,
            wiring.button_net(name),
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
            TestPoint(reference),
            part_key="TEST_POINT",
            assembly="controls",
            library="TESTPOINT",
            value=net,
            description=description,
        )
        connect(board, net, probe.pin(p.TestPointPin.PROBE))
