"""The mechanical board assembly, composed from real named components.

The main PCB and its mounted parts are imported from KiCad. Shared definitions
keep dimensions and interfaces readable for both domains; CAD builds the
enclosure and off-board assembly from those definitions.
"""

from pathlib import Path

from cad.board.wiring import wire_route
from cad.components.electronics.connector_mate import ConnectorMate
from cad.components.electronics.display_module import DisplayModule
from cad.components.electronics.harness_wire import HarnessWire
from cad.components.electronics.host_board import HostBoard
from cad.components.electronics.panel_dc_jack import PanelDcJack
from cad.components.electronics.panel_power_switch import PanelPowerSwitch
from cad.components.electronics.pcb_assembly import PcbAssembly
from cad.components.electronics.tab_receptacle import TabReceptacle
from cad.components.printable.board_case import BoardCase
from cad.components.printable.button_cap import ButtonCap
from cad.components.printable.tile_plate import TilePlate
from cad.harness.base.component import Component
from cad.harness.base.pcb import PcbSnapshot
from cad.harness.base.registry import ModelRegistry
from shared.electronics.harness import HARNESSES
from shared.panel_buttons import PANEL_BUTTONS


class Board(ModelRegistry):
    def __init__(
        self, pcb: PcbSnapshot | None = None, source: Path | None = None
    ) -> None:
        super().__init__()
        source = (
            source
            or Path(__file__).resolve().parents[2] / "pcb/generated/chess-board.glb"
        )
        self.pcb_definition = (
            PcbSnapshot.read(source.with_name("pcb-components.json"))
            if pcb is None
            else pcb
        )
        self.case = self.add(BoardCase())
        self.plate = self.add(TilePlate())
        self.pcb = self.add(
            PcbAssembly(
                source,
                self.pcb_definition,
            )
        )
        self.host = self.add(HostBoard())
        self.display = self.add(DisplayModule())
        self.button_caps = tuple(
            self.add(ButtonCap(button)) for button in PANEL_BUTTONS
        )
        self.pcb_parts = {part.reference: part for part in self.pcb_definition.parts}
        self.sensors = {
            name: self.pcb_parts[reference]
            for name, reference in self.pcb_definition.sensors.items()
        }
        self.leds = {
            name: self.pcb_parts[reference]
            for name, reference in self.pcb_definition.leds.items()
        }
        self.buttons = {
            name: self.pcb_parts[reference]
            for name, reference in self.pcb_definition.buttons.items()
        }
        self.panel_parts = (self.add(PanelDcJack()), self.add(PanelPowerSwitch()))
        self.receptacles = tuple(self.add(TabReceptacle(i)) for i in (1, 2))
        self.connector_mates = tuple(
            self.add(ConnectorMate(self.pcb_parts[reference]))
            for reference in ("J4", "J2")
        )
        self.harness_wires = tuple(
            self.add(
                HarnessWire(
                    wire,
                    wire_route(wire, self.pcb_definition),
                    (
                        wire.connector,
                        f"Mate_{wire.connector}",
                        "Proxy_Display_Module"
                        if wire.far_part == "OLED_MODULE"
                        else f"ROCKER_RECEPTACLE_{int(wire.cavity) - 2}"
                        if wire.far_part == "POWER_SWITCH"
                        else wire.far_part,
                    ),
                )
            )
            for wires in HARNESSES.values()
            for wire in wires
        )
        self.validate()

    @property
    def electronics(
        self,
    ) -> tuple[Component, ...]:
        return (
            self.pcb,
            self.host,
            self.display,
            *self.button_caps,
            *self.panel_parts,
            *self.connector_mates,
            *self.receptacles,
            *self.harness_wires,
        )
