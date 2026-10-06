"""Host GPIO, level shifting, display, and twelve direct panel buttons.

Role: the 'controls' assembly: Pi header J1, OLED header J2, the AHCT125 level shifter U5
and its LED data termination R9, the LED-line pull-downs R17/R18, the LED rail switch (`led_switch.py`), the panel buttons
and the test points. Net names come from `shared/wiring.py` and pin identities from
`shared/electronics`, so GPIO assignments have one source.
"""

from __future__ import annotations

import pcbnew

from pcb.definition.assemblies.led_switch import add_led_switch
from pcb.definition.assemblies.power import add_strip
from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts import catalog as parts
from shared import dimensions, wiring
from shared import electronics as p
from shared.panel_buttons import PANEL_BUTTONS

ASSEMBLY_PART_COUNT = 23


def add_controls(board: pcbnew.BOARD) -> None:
    """Place and wire everything on the control strip and the Pi socket.

    J1 (bottom side, Pi socket), J2 (OLED harness header), U5 (the 3.3 V to 5 V buffer for the
    LED chain, with decoupling C7), R9 (source termination of the first LED data link), the LED
    rail switch, the twelve buttons and the test points. Pins the design does not use are
    connected to explicit no-connects: leaving a pin out is never treated as "unused".
    """
    host = place(
        board,
        parts.PI_ZERO_HEADER_PART,
        "J1",
        # Derived from the Pi transform (shared case.py): the socket hangs the Pi
        # below the board; footprint pin 1->39 runs along local -Y, the Pi
        # drawing's along +X, hence the extra quarter turn.
        at=dimensions.PI_HEADER_CENTER_MM,
        rotation=(dimensions.PI_ROTATION_DEG + 90.0) % 360.0,
        bottom=True,
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
    # S5: the I2C pull-ups are the Pi's own (Zero 2 W R23/R24 1.8 kOhm); R1/R2 are
    # retired. R9 source-terminates the first LED data link (B.Cu, about 102 ohm).
    termination = add_strip(
        board,
        parts.RES_56_PART,
        "R9",
        assembly="controls",
        purpose="LED data source termination",
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
        display.pin(p.OledHeaderPin.MOUNTING_TAB_A),
        display.pin(p.OledHeaderPin.MOUNTING_TAB_B),
        buffer.pin(p.Ahct125Pin.GROUND),
        bypass.pin(p.CapacitorPin.RETURN_OR_ELECTRODE_B),
        *(
            buffer.pin(pin)
            for pin in (
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
    )
    connect(
        board,
        wiring.SCL_NET,
        host.pin(p.RaspberryPiHeaderPin.I2C_SCL),
        display.pin(p.OledHeaderPin.I2C_CLOCK),
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
    connect(
        board,
        wiring.LED_DATA_BUFFER_NET,
        buffer.pin(p.Ahct125Pin.BUFFER_1_OUTPUT),
        termination.pin(p.ResistorPin.TERMINAL_B),
    )
    connect(board, wiring.LED_DATA_NET, termination.pin(p.ResistorPin.TERMINAL_A))
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
    ):
        no_connect(board, host.pin(pin))
    # S6: LED_EN (pin 37) switches the LED rail; LED_EN_N also enables U5's buffers.
    add_led_switch(board, host, buffer)
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
        pin = button.header_pin
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
    # S6d (reviewer-s6c m2): U75 keeps U5's LED outputs Hi-Z until LED_5V is up,
    # so 10 kOhm pull-downs hold U6's DI/CI low instead of letting them float.
    for reference, net in (
        ("R17", wiring.LED_DATA_NET),
        ("R18", wiring.LED_CLOCK_NET),
    ):
        pull_down = add_strip(
            board,
            parts.RES_10K_PART,
            reference,
            assembly="controls",
            purpose=f"{net} pull-down while the buffer is Hi-Z",
        )
        connect(board, net, pull_down.pin(p.ResistorPin.TERMINAL_A))
        connect(board, "GND", pull_down.pin(p.ResistorPin.TERMINAL_B))
