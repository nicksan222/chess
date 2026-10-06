"""Tests beside the component base classes and automatic registration."""

import unittest
from enum import StrEnum
from typing import cast

from pcb.harness.base.component import BoardComponent, ComponentDefinition
from pcb.harness.base.connections import NetConnection, NoConnect, PinConnection
from pcb.harness.base.geometry import Courtyard, Placement
from pcb.harness.base.net import Net
from pcb.harness.base.pcbnew.land_pattern import LandPattern
from pcb.harness.base.pcbnew.pad import Pad
from pcb.harness.base.pcbnew.point import Point
from pcb.harness.base.product import Product
from pcb.harness.base.registry import BoardRegistry
from pcb.harness.base.spice.model import SpiceModel


class Nets(Net):
    POWER = "+3V3"
    SIGNAL = "SIGNAL"
    WRONG = "WRONG"


class Pin(StrEnum):
    VCC = "1"
    OUT = "2"


def definition() -> ComponentDefinition[Pin]:
    return ComponentDefinition(
        Product("DEVICE", "Maker", "D-1", "SMD", (2.0, 1.0, 0.5), "sheet"),
        Pin,
        Courtyard(3.0, 2.0),
    )


class ComponentTest(unittest.TestCase):
    """Prove definitions validate reusable facts and instances register atomically."""

    def test_complete_component_registers_itself(self) -> None:
        """A complete instance appears in the registry after construction."""
        board = BoardRegistry()
        BoardComponent(
            board,
            "U1",
            definition(),
            Placement(0.0, 0.0),
            "driver",
            {Pin.VCC: NetConnection(Nets.POWER), Pin.OUT: NoConnect("unused")},
        )
        self.assertEqual(board.net_members(Nets.POWER)[0].reference, "U1")

    def test_missing_pin_does_not_register_partial_component(self) -> None:
        """A missing pin fails before any instance reaches the registry."""
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "missing pins"):
            BoardComponent(
                board,
                "U1",
                definition(),
                Placement(0.0, 0.0),
                "driver",
                {Pin.VCC: NetConnection(Nets.POWER)},
            )
        self.assertEqual(board.net_members(Nets.POWER), ())

    def test_pin_from_another_enum_is_rejected_even_if_number_matches(self) -> None:
        """Pin enum identity matters even when the printed number matches."""

        class OtherPin(StrEnum):
            OUT = "2"

        with self.assertRaisesRegex(ValueError, "another kind"):
            BoardComponent(
                BoardRegistry(),
                "U1",
                definition(),
                Placement(0.0, 0.0),
                "driver",
                {
                    Pin.VCC: NetConnection(Nets.POWER),
                    OtherPin.OUT: NetConnection(Nets.SIGNAL),
                },
            )

    def test_model_terminals_must_be_this_kinds_pins(self) -> None:
        """A reusable model may expose only its definition's pin enum."""

        class OtherPin(StrEnum):
            VCC = "1"

        with self.assertRaisesRegex(ValueError, "belong"):
            ComponentDefinition(
                definition().product,
                Pin,
                Courtyard(3.0, 2.0),
                SpiceModel("device", (OtherPin.VCC,)),
            )

    def test_land_pattern_must_use_exact_pin_enum(self) -> None:
        """A land pattern must describe the same typed pins as its definition."""

        class OtherPin(StrEnum):
            VCC = "1"
            OUT = "2"

        pattern = LandPattern(
            OtherPin,
            (
                Pad(OtherPin.VCC, Point(-1, 0), 0.5, 0.5),
                Pad(OtherPin.OUT, Point(1, 0), 0.5, 0.5),
            ),
        )
        with self.assertRaisesRegex(ValueError, "land pattern pins"):
            ComponentDefinition(
                definition().product, Pin, Courtyard(3, 2), land_pattern=pattern
            )  # type: ignore[arg-type]

    def test_copper_pads_must_fit_within_declared_courtyard(self) -> None:
        """Declared copper cannot extend beyond its component keep-clear box."""
        pattern = LandPattern(
            Pin,
            (
                Pad(Pin.VCC, Point(-1.4, 0), 0.5, 0.5),
                Pad(Pin.OUT, Point(1.4, 0), 0.5, 0.5),
            ),
        )
        with self.assertRaisesRegex(ValueError, "courtyard"):
            ComponentDefinition(
                definition().product, Pin, Courtyard(3, 2), land_pattern=pattern
            )

    def test_product_body_must_fit_inside_its_courtyard(self) -> None:
        """A small clearance cannot hide a body that crosses the board edge."""
        with self.assertRaisesRegex(ValueError, "body.*courtyard"):
            ComponentDefinition(
                Product("LARGE", "Maker", "L-1", "SMD", (20, 20, 1), "sheet"),
                Pin,
                Courtyard(2, 2),
            )

    def test_non_pattern_value_is_rejected_cleanly(self) -> None:
        """A malformed physical definition yields a useful authoring error."""
        with self.assertRaisesRegex(ValueError, "land pattern"):
            ComponentDefinition(
                definition().product,
                Pin,
                Courtyard(3, 2),
                land_pattern=cast(LandPattern[Pin], object()),
            )

    def test_input_pin_map_is_copied_before_registration(self) -> None:
        """Mutating the caller's input map cannot mutate a registered instance."""
        board = BoardRegistry()
        pins = {Pin.VCC: NetConnection(Nets.POWER), Pin.OUT: NoConnect("unused")}
        BoardComponent(board, "U1", definition(), Placement(0, 0), "driver", pins)
        pins[Pin.VCC] = NetConnection(Nets.WRONG)
        self.assertEqual(board.net_members(Nets.POWER)[0].reference, "U1")
        self.assertEqual(board.net_members(Nets.WRONG), ())

    def test_bad_connection_does_not_register(self) -> None:
        """An invalid connection cannot leave a partially registered part."""
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "invalid pin connection"):
            BoardComponent(
                board,
                "U1",
                definition(),
                Placement(0, 0),
                "driver",
                {
                    Pin.VCC: NetConnection(Nets.POWER),
                    Pin.OUT: cast(PinConnection, None),
                },
            )
        self.assertEqual(board.net_members(Nets.POWER), ())

    def test_component_exposes_its_declared_simulation_model(self) -> None:
        """The instance exposes the reusable model selected by its definition."""
        model = SpiceModel("device", (Pin.VCC, Pin.OUT))
        kind = ComponentDefinition(
            definition().product, Pin, Courtyard(3.0, 2.0), model
        )
        component = BoardComponent(
            BoardRegistry(),
            "U1",
            kind,
            Placement(0, 0),
            "driver",
            {Pin.VCC: NetConnection(Nets.POWER), Pin.OUT: NetConnection(Nets.SIGNAL)},
        )
        self.assertIs(component.simulation_model(), model)
