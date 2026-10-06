"""A deliberately small board example built only from harness declarations.

This is a review and test fixture, not a recommended purchasable design. Its
two ideal 1 kΩ resistors form a 3.3 V divider. The same typed circuit supplies
an ngspice operating-point check and a KiCad board-only project. There are no
connectors or power source footprints, so the board is not a usable assembly.
"""

from __future__ import annotations

from pcb.harness import (
    BoardOutline,
    Circuit,
    ComponentDefinition,
    CopperLayer,
    Courtyard,
    LandPattern,
    Net,
    Pad,
    Placement,
    Point,
    Product,
    Trace,
)
from pcb.harness.components.resistor import Resistor, ResistorPin


class TinyNet(Net):
    """Every electrical network in this example has one typed identity."""

    POWER = "+3V3"
    MID = "MID"
    GROUND = "GND"


def tiny_divider() -> Circuit[TinyNet]:
    """Build the physical and simulated forms from one circuit declaration.

    Pad positions are package-local millimetres, while resistor placements
    and the MID trace use board-centred millimetres. R1 and R2 share a single
    reusable product/land-pattern definition; their references and nets are
    instance facts. The SPICE assertion checks the idealized midpoint only.
    """
    board = Circuit(TinyNet, outline=BoardOutline(20, 10))
    resistor = ComponentDefinition(
        Product("DEMO-1K", "Demo", "1K-0603", "0603", (1.6, 0.8, 0.5), "example"),
        ResistorPin,
        Courtyard(2.4, 1.4),
        land_pattern=LandPattern(
            ResistorPin,
            (
                Pad(ResistorPin.TERMINAL_A, Point(-0.8, 0), 0.7, 0.8),
                Pad(ResistorPin.TERMINAL_B, Point(0.8, 0), 0.7, 0.8),
            ),
        ),
    )
    board.place(
        Resistor,
        reference="R1",
        definition=resistor,
        placement=Placement(-2, 0),
        purpose="upper divider leg",
        pins={
            ResistorPin.TERMINAL_A: TinyNet.POWER,
            ResistorPin.TERMINAL_B: TinyNet.MID,
        },
        resistance_ohms=1000,
        tolerance_percent=1,
    )
    lower = board.place(
        Resistor,
        reference="R2",
        definition=resistor,
        placement=Placement(2, 0),
        purpose="lower divider leg",
        pins={
            ResistorPin.TERMINAL_A: TinyNet.MID,
            ResistorPin.TERMINAL_B: TinyNet.GROUND,
        },
        resistance_ohms=1000,
        tolerance_percent=1,
    )
    # This single explicit track joins the two MID pads on top copper.
    board.trace(
        Trace(TinyNet.MID, Point(-1.2, 0), Point(1.2, 0), CopperLayer.TOP, 0.25)
    )
    with board.check(
        "nominal", ground=TinyNet.GROUND, purpose="3.3 V divider"
    ) as check:
        check.dc_supply("VPOWER", TinyNet.POWER, TinyNet.GROUND, volts=3.3)
        check.voltage_at(
            lower,
            ResistorPin.TERMINAL_A,
            between=(1.5, 1.8),
            because="two equal ideal resistors should divide 3.3 V in half",
        )
    return board
