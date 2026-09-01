"""Small KiCad drawing primitives shared by board-generation stages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from base import footprint as footprint_base
from base import rules
from base.connectivity import ConnectionGraph, EndpointKey
from base.kicad.api import pcbnew
from shared.components import COMPONENTS

if TYPE_CHECKING:
    from base.design import BoardDesign, ComponentInstance

ORIGIN_X_MM = 200.0
ORIGIN_Y_MM = 220.0


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    """Translate shared, centre-origin coordinates into KiCad coordinates."""
    return pcbnew.VECTOR2I(
        pcbnew.FromMM(x + ORIGIN_X_MM),
        pcbnew.FromMM(ORIGIN_Y_MM - y),
    )


def add_trace(
    board,
    net,
    start,
    end,
    layer=pcbnew.F_Cu,
    width: float = rules.TRACE_WIDTH_MM,
) -> None:
    """Add one exact point-to-point copper segment."""
    trace = pcbnew.PCB_TRACK(board)
    trace.SetStart(start)
    trace.SetEnd(end)
    trace.SetWidth(pcbnew.FromMM(width))
    trace.SetLayer(layer)
    trace.SetNet(net)
    board.Add(trace)


def add_via(board, net, at) -> None:
    """Add one standard through-via at an exact position."""
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(at)
    via.SetWidth(pcbnew.FromMM(rules.VIA_PAD_MM))
    via.SetDrill(pcbnew.FromMM(rules.VIA_DRILL_MM))
    via.SetNet(net)
    board.Add(via)


class KiCadBoard:
    """Object-oriented adapter around the native KiCad board and connection graph."""

    def __init__(self, design: BoardDesign | ConnectionGraph) -> None:
        pcbnew.KIID.SeedGenerator(0x43484553)
        self.native = pcbnew.BOARD()
        self.design = design if hasattr(design, "components") else None
        self.connections = design.connections if self.design else design
        self.nets = self._add_nets(self.connections.names)
        self.pads: dict[EndpointKey, object] = {}
        self._configure_rules()

    def _configure_rules(self) -> None:
        self.native.SetCopperLayerCount(rules.COPPER_LAYERS)
        settings = self.native.GetDesignSettings()
        settings.SetBoardThickness(pcbnew.FromMM(rules.BOARD_THICKNESS_MM))
        settings.m_MinClearance = pcbnew.FromMM(rules.CLEARANCE_MM)
        settings.m_TrackMinWidth = pcbnew.FromMM(rules.TRACE_WIDTH_MM)
        settings.m_HoleClearance = pcbnew.FromMM(rules.HOLE_CLEARANCE_MM)
        settings.m_HoleToHoleMin = pcbnew.FromMM(rules.HOLE_TO_HOLE_MM)
        settings.m_CopperEdgeClearance = pcbnew.FromMM(rules.POUR_TO_OUTLINE_MM)
        settings.m_ViasMinSize = pcbnew.FromMM(rules.VIA_PAD_MM)
        settings.m_ViasMinAnnularWidth = pcbnew.FromMM(
            rules.annular_ring(rules.VIA_PAD_MM, rules.VIA_DRILL_MM)
        )
        settings.m_MinThroughDrill = pcbnew.FromMM(rules.PCBWAY_MIN_DRILL_MM)
        settings.m_SilkClearance = pcbnew.FromMM(rules.PCBWAY_MIN_MASK_DAM_MM)
        settings.m_SolderMaskMinWidth = pcbnew.FromMM(rules.PCBWAY_MIN_MASK_DAM_MM)

    def _add_nets(self, names: tuple[str, ...]) -> dict[str, object]:
        nets = {}
        for code, name in enumerate(names, 1):
            net = pcbnew.NETINFO_ITEM(self.native, name, code)
            self.native.Add(net)
            nets[name] = net
        return nets

    def attach(self, component: ComponentInstance) -> None:
        """Materialize one typed component instance on the native board."""
        self._attach_placement(
            component.placement,
            component.spec.part_key,
            component.spec.package,
        )

    def _attach_placement(self, item, part_key: object, package: str) -> None:
        """The only component-to-pcbnew materialization implementation."""
        if not isinstance(part_key, str):
            raise ValueError(f"{item.reference}: missing product key")
        spec = COMPONENTS[part_key]
        if spec.package != package or package != item.package:
            raise ValueError(
                f"{item.reference}: {spec.mpn} requires {spec.package!r}, "
                f"not {item.package!r}"
            )

        module = pcbnew.FOOTPRINT(self.native)
        module.SetReference(item.reference)
        module.SetValue(spec.mpn)
        module.SetLibDescription(f"{spec.manufacturer} {spec.mpn}: {spec.description}")
        module.Reference().SetVisible(False)
        module.Value().SetVisible(False)
        module.SetPosition(point(item.x, item.y))
        module.SetOrientationDegrees(item.rotation)
        self.native.Add(module)
        self._add_package_outlines(module, item)

        for logical, number, (x, y), definition in item.pads():
            pad = self._new_pad(module, number, x, y, definition)
            endpoint = (item.reference, logical)
            pad.SetNet(self.net(self.connections.net_name(endpoint)))
            module.Add(pad)
            self.pads[endpoint] = pad

    def _add_package_outlines(self, module, item) -> None:
        width, height = item.footprint.courtyard_at(item.rotation)
        for layer, inset in (
            (pcbnew.F_CrtYd, 0.0),
            (pcbnew.F_Fab, footprint_base.COURTYARD_MARGIN_MM),
        ):
            x0, x1 = item.x - width / 2 + inset, item.x + width / 2 - inset
            y0, y1 = item.y - height / 2 + inset, item.y + height / 2 - inset
            corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
            for index, start in enumerate(corners):
                line = pcbnew.PCB_SHAPE(module)
                line.SetShape(pcbnew.SHAPE_T_SEGMENT)
                line.SetStart(point(*start))
                line.SetEnd(point(*corners[(index + 1) % 4]))
                line.SetLayer(layer)
                width = (
                    rules.COURTYARD_LINE_MM
                    if layer == pcbnew.F_CrtYd
                    else rules.FAB_LINE_MM
                )
                line.SetWidth(pcbnew.FromMM(width))
                module.Add(line)

    @staticmethod
    def _new_pad(module, number, x, y, definition):
        pad = pcbnew.PAD(module)
        pad.SetNumber(number)
        pad.SetPosition(point(x, y))
        pad.SetSize(
            pcbnew.VECTOR2I(
                pcbnew.FromMM(definition.width),
                pcbnew.FromMM(definition.height),
            )
        )
        pad.SetShape(
            {
                footprint_base.ROUND: pcbnew.PAD_SHAPE_CIRCLE,
                footprint_base.RECT: pcbnew.PAD_SHAPE_RECT,
                footprint_base.OBLONG: pcbnew.PAD_SHAPE_OVAL,
            }[definition.shape]
        )
        if definition.plated_through:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            drill_width, drill_height = definition.drill_size
            pad.SetDrillSize(
                pcbnew.VECTOR2I(
                    pcbnew.FromMM(drill_width),
                    pcbnew.FromMM(drill_height),
                )
            )
            if drill_width != drill_height:
                pad.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_OBLONG)
            pad.SetLayerSet(pad.PTHMask())
        else:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pad.SMDMask())
        pad.SetLocalSolderMaskMargin(pcbnew.FromMM(rules.MASK_EXPANSION_MM))
        return pad

    def net(self, name: str):
        try:
            return self.nets[name]
        except KeyError as error:
            raise KeyError(f"KiCad board has no net {name!r}") from error

    def pad(self, endpoint: EndpointKey):
        try:
            return self.pads[endpoint]
        except KeyError as error:
            raise KeyError(f"KiCad board has no pad for {endpoint}") from error

    def trace(
        self,
        net,
        start,
        end,
        layer=pcbnew.F_Cu,
        width: float = rules.TRACE_WIDTH_MM,
    ) -> None:
        add_trace(self.native, net, start, end, layer, width)

    def via(self, net, at) -> None:
        add_via(self.native, net, at)
