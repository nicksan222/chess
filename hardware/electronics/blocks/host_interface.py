"""The Pi socket and the one buffer between it and the LED chain.

The Raspberry Pi Zero 2 W is the only processor on the board: it reads the
expanders over I2C, shifts the LED frame out over SPI, and reads the panel
buttons on plain GPIO lines. There is no firmware to write and no second
toolchain, because there is no second processor.

The board also takes its 3.3 V from this header rather than carrying a
regulator, which the five expander-and-display loads are small enough to allow.
"""

from __future__ import annotations

from components import (
    CERAMIC_DISC,
    LEVEL_BUFFER,
    PI_HEADER,
    SOCKET_DIP14,
    capacitor,
    resistor,
    testpoint,
)
from components.level_buffer import (
    GND_PIN as BUFFER_GND_PIN,
    SPARE_CHANNELS,
    USED_CHANNELS,
    VCC_PIN as BUFFER_VCC_PIN,
)
from components.pi_header import (
    GND_PINS,
    GPIO_TO_PIN,
    SIGNAL_PINS,
    SUPPLY_3V3_PINS,
    SUPPLY_5V_PINS,
)
from core.canvas import Schematic
from core.names import (
    BUTTON_GPIO,
    LED_CLOCK_NET,
    LED_DATA_NET,
    SCL_GPIO,
    SCL_NET,
    SDA_GPIO,
    SDA_NET,
    SENSE_IRQ_GPIO,
    SENSE_IRQ_NET,
    SPI_CLOCK_GPIO,
    SPI_CLOCK_NET,
    SPI_DATA_GPIO,
    SPI_DATA_NET,
    button_net,
)


def pi_pin_nets() -> dict[str, str]:
    """Every header pin that carries something, by pin number."""
    nets = {pin: "+3V3" for pin in SUPPLY_3V3_PINS}
    nets.update({pin: "+5V" for pin in SUPPLY_5V_PINS})
    nets.update({pin: "GND" for pin in GND_PINS})
    nets[GPIO_TO_PIN[SDA_GPIO]] = SDA_NET
    nets[GPIO_TO_PIN[SCL_GPIO]] = SCL_NET
    nets[GPIO_TO_PIN[SENSE_IRQ_GPIO]] = SENSE_IRQ_NET
    nets[GPIO_TO_PIN[SPI_DATA_GPIO]] = SPI_DATA_NET
    nets[GPIO_TO_PIN[SPI_CLOCK_GPIO]] = SPI_CLOCK_NET
    for name, gpio in BUTTON_GPIO.items():
        nets[GPIO_TO_PIN[gpio]] = button_net(name)
    return nets


def add_host_interface(
    sch: Schematic, *, origin_x: float = 0.0, origin_y: float = 0.0
) -> None:
    sch.place(PI_HEADER, "J1", origin_x, origin_y)

    nets = pi_pin_nets()
    for pin, net in nets.items():
        sch.label_pin(net, "J1", pin)
    for pin in SIGNAL_PINS:
        if pin not in nets:
            sch.nc(*sch.pin("J1", pin))

    # The Pi's own 1.8 kohm pull-ups sit right at the fast-mode rise-time limit
    # once five devices and 320 mm of trace are on the bus. These bring it back.
    sch.place(resistor("4.7k", "I2C pull-up"), "R1", origin_x + 30.0, origin_y + 6.0)
    sch.place(resistor("4.7k", "I2C pull-up"), "R2", origin_x + 30.0, origin_y + 1.0)
    sch.label_pin("+3V3", "R1", "1")
    sch.label_pin(SDA_NET, "R1", "2")
    sch.label_pin("+3V3", "R2", "1")
    sch.label_pin(SCL_NET, "R2", "2")

    _add_buffer(sch, origin_x + 30.0, origin_y - 16.0)


def _add_buffer(sch: Schematic, x: float, y: float) -> None:
    sch.place(LEVEL_BUFFER, "U5", x, y)
    sch.place(SOCKET_DIP14, "SKT5", x, y - 22.0)
    sch.place(
        capacitor(CERAMIC_DISC, "100nF", "Buffer decoupling capacitor"),
        "C7",
        x + 12.0,
        y - 20.0,
    )

    sch.label_pin("+5V", "U5", BUFFER_VCC_PIN)
    sch.label_pin("GND", "U5", BUFFER_GND_PIN)
    sch.label_pin("+5V", "C7", "1")
    sch.label_pin("GND", "C7", "2")

    channels = (
        (SPI_DATA_NET, LED_DATA_NET),
        (SPI_CLOCK_NET, LED_CLOCK_NET),
    )
    for (input_net, output_net), (enable_pin, input_pin, output_pin) in zip(
        channels, USED_CHANNELS
    ):
        # Output enable is active low, so a used channel ties it to ground.
        sch.label_pin("GND", "U5", enable_pin)
        sch.label_pin(input_net, "U5", input_pin)
        sch.label_pin(output_net, "U5", output_pin)

    for enable_pin, input_pin, output_pin in SPARE_CHANNELS:
        # A spare channel is held disabled with its input tied off, rather than
        # left floating to oscillate and inject noise into the shared supply.
        sch.label_pin("+5V", "U5", enable_pin)
        sch.label_pin("GND", "U5", input_pin)
        sch.nc(*sch.pin("U5", output_pin))

    sch.place(
        testpoint(LED_DATA_NET, "Buffered LED data test point"), "TP3", x + 15.0, y + 4.0
    )
    sch.place(
        testpoint(LED_CLOCK_NET, "Buffered LED clock test point"),
        "TP4",
        x + 15.0,
        y - 0.5,
    )
    sch.label_pin(LED_DATA_NET, "TP3", "1")
    sch.label_pin(LED_CLOCK_NET, "TP4", "1")

    sch.note(
        "SK9822 needs 0.7 x 5 V for a logic high; the Pi drives 3.3 V.",
        x - 4.0,
        y - 27.0,
    )
