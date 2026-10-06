"""Tests beside registry-level cross-component checks."""

import unittest
from enum import StrEnum

from pcb.harness import (
    BoardComponent,
    BoardOutline,
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    DcVoltage,
    Endpoint,
    Limit,
    NetConnection,
    NoConnect,
    Observation,
    OperatingPoint,
    Placement,
    Product,
    Side,
    SpiceRequirement,
    SpiceScenario,
    VoltageAt,
    VoltageSource,
)
from pcb.harness.base.net import Net
from pcb.harness.base.spice.analysis import AcSweep
from pcb.harness.base.spice.measurement import CurrentThrough
from pcb.harness.base.spice.source import CurrentSource


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"
    A = "A"
    B = "B"


class OtherNets(Net):
    GROUND = "GND"


class Pin(StrEnum):
    ONLY = "1"


KIND = ComponentDefinition(
    Product("P", "Maker", "P-1", "SMD", (1.0, 1.0, 1.0), "sheet"),
    Pin,
    Courtyard(2.0, 2.0),
)


class RegistryTest(unittest.TestCase):
    """Prove registry validation catches cross-component and SPICE references."""

    def test_same_label_from_different_enum_cannot_join_board(self) -> None:
        """One registry cannot mix distinct Net enum classes."""
        board = BoardRegistry()
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "one",
            {Pin.ONLY: NetConnection(Nets.GROUND)},
        )
        BoardComponent(
            board,
            "U2",
            KIND,
            Placement(1, 0),
            "two",
            {Pin.ONLY: NetConnection(OtherNets.GROUND)},
        )
        with self.assertRaisesRegex(ValueError, "one Net enum"):
            board.validate()

    def test_two_unknown_source_nets_have_readable_error(self) -> None:
        """Validation reports every source net absent from component topology."""
        board = BoardRegistry()
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "ground",
            {Pin.ONLY: NetConnection(Nets.GROUND)},
        )
        SpiceScenario(
            board,
            "normal",
            "power",
            Nets.GROUND,
            OperatingPoint(),
            (VoltageSource("V1", Nets.A, Nets.B, DcVoltage(3.3)),),
        )
        with self.assertRaisesRegex(ValueError, "unknown nets.*A.*B"):
            board.validate()

    def test_duplicate_reference_fails_during_construction(self) -> None:
        """References are unique at registration time."""
        board = BoardRegistry()
        BoardComponent(
            board, "U1", KIND, Placement(0, 0), "one", {Pin.ONLY: NetConnection(Nets.A)}
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            BoardComponent(
                board,
                "U1",
                KIND,
                Placement(1, 0),
                "two",
                {Pin.ONLY: NetConnection(Nets.B)},
            )

    def test_overlapping_courtyards_fail_registration_without_partial_part(
        self,
    ) -> None:
        """Every new placed part is compared with previously registered parts."""
        board = BoardRegistry(outline=BoardOutline(10, 10))
        BoardComponent(board, "U1", KIND, Placement(0, 0), "first", {Pin.ONLY: Nets.A})
        with self.assertRaisesRegex(ValueError, "U1.*U2.*courtyard overlap"):
            BoardComponent(
                board, "U2", KIND, Placement(1, 0), "second", {Pin.ONLY: Nets.B}
            )
        self.assertEqual(tuple(part.reference for part in board.components()), ("U1",))

    def test_touching_and_opposite_side_courtyards_register(self) -> None:
        """Parts may abut and may occupy opposite faces at the same XY point."""
        board = BoardRegistry(outline=BoardOutline(10, 10))
        for reference, placement in (
            ("U1", Placement(0, 0)),
            ("U2", Placement(2, 0)),
            ("U3", Placement(0, 0, side=Side.BOTTOM)),
        ):
            BoardComponent(
                board, reference, KIND, placement, "fixture", {Pin.ONLY: Nets.A}
            )
        board.validate_physical()
        self.assertEqual(len(board.components()), 3)

    def test_courtyard_outside_outline_fails_before_registration(self) -> None:
        """An out-of-bounds placement cannot enter a physical board registry."""
        board = BoardRegistry(outline=BoardOutline(10, 10))
        with self.assertRaisesRegex(ValueError, "U1.*courtyard.*outline"):
            BoardComponent(
                board, "U1", KIND, Placement(4.5, 0), "edge", {Pin.ONLY: Nets.A}
            )
        self.assertEqual(board.components(), ())

    def test_peer_must_share_the_declared_net(self) -> None:
        """An exact peer declaration must agree with the peer's net."""
        board = BoardRegistry()
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "one",
            {Pin.ONLY: NetConnection(Nets.A, (Endpoint("U2", "1"),))},
        )
        BoardComponent(
            board, "U2", KIND, Placement(1, 0), "two", {Pin.ONLY: NetConnection(Nets.B)}
        )
        with self.assertRaisesRegex(ValueError, "U1/1 expects U2/1"):
            board.validate()

    def test_requirement_must_name_a_registered_scenario(self) -> None:
        """A measurement cannot target a scenario that was never declared."""
        board = BoardRegistry()
        requirement = SpiceRequirement(
            "missing",
            VoltageAt(Endpoint("U1", "1")),
            Observation.SINGLE,
            Limit(3.1, 3.5),
            "supply",
        )
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "one",
            {Pin.ONLY: NetConnection(Nets.POWER)},
            (requirement,),
        )
        with self.assertRaisesRegex(ValueError, "unknown SPICE scenario"):
            board.validate()

    def test_source_nets_must_exist_on_the_declared_board(self) -> None:
        """A source cannot introduce nets absent from the board pin maps."""
        board = BoardRegistry()
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "one",
            {Pin.ONLY: NetConnection(Nets.GROUND)},
        )
        SpiceScenario(
            board,
            "normal",
            "power",
            Nets.GROUND,
            OperatingPoint(),
            (VoltageSource("V1", Nets.POWER, Nets.GROUND, DcVoltage(3.3)),),
        )
        with self.assertRaisesRegex(ValueError, "unknown nets"):
            board.validate()

    def test_cannot_measure_intentionally_open_pin(self) -> None:
        """No-connect pins cannot be used as simulation measurement points."""
        board = BoardRegistry()
        requirement = SpiceRequirement(
            "normal",
            VoltageAt(Endpoint("U1", "1")),
            Observation.SINGLE,
            Limit(0, 1),
            "probe",
        )
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "one",
            {Pin.ONLY: NoConnect("unused")},
            (requirement,),
        )
        BoardComponent(
            board,
            "U2",
            KIND,
            Placement(0, 0),
            "ground",
            {Pin.ONLY: NetConnection(Nets.GROUND)},
        )
        SpiceScenario(board, "normal", "power", Nets.GROUND, OperatingPoint(), ())
        with self.assertRaisesRegex(ValueError, "cannot measure unconnected"):
            board.validate()

    def test_ac_sweep_requires_an_ac_excitation(self) -> None:
        """An AC analysis requires at least one AC-enabled voltage source."""
        board = BoardRegistry()
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "power",
            {Pin.ONLY: NetConnection(Nets.POWER)},
        )
        BoardComponent(
            board,
            "U2",
            KIND,
            Placement(0, 0),
            "ground",
            {Pin.ONLY: NetConnection(Nets.GROUND)},
        )
        SpiceScenario(
            board,
            "response",
            "frequency response",
            Nets.GROUND,
            AcSweep(10, 10000, 20),
            (VoltageSource("V1", Nets.POWER, Nets.GROUND, DcVoltage(0)),),
        )
        with self.assertRaisesRegex(ValueError, "AC excitation"):
            board.validate()

    def test_current_probe_must_name_a_voltage_source(self) -> None:
        """A current probe names a voltage source whose branch current exists."""
        board = BoardRegistry()
        requirement = SpiceRequirement(
            "normal",
            CurrentThrough("ILOAD"),
            Observation.SINGLE,
            Limit(-1, 1),
            "source current",
        )
        BoardComponent(
            board,
            "U1",
            KIND,
            Placement(0, 0),
            "power",
            {Pin.ONLY: NetConnection(Nets.POWER)},
            (requirement,),
        )
        BoardComponent(
            board,
            "U2",
            KIND,
            Placement(0, 0),
            "ground",
            {Pin.ONLY: NetConnection(Nets.GROUND)},
        )
        SpiceScenario(
            board,
            "normal",
            "power",
            Nets.GROUND,
            OperatingPoint(),
            (CurrentSource("ILOAD", Nets.POWER, Nets.GROUND, 0.01),),
        )
        with self.assertRaisesRegex(ValueError, "voltage source"):
            board.validate()
