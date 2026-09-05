"""Native board authoring, checked logical-pin assignment, and KiCad serialization."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew

from pcb.definition import rules
from pcb.definition.output.symbols import ROOT_UUID, uid
from pcb.definition.parts.catalog import MODELS, TEMPLATES
from pcb.definition.rules import Net
from shared import dimensions, wiring
from shared.components import COMPONENTS
from shared.electronics import BoundPin, EndpointResolver

ORIGIN_X_MM = 200.0
ORIGIN_Y_MM = 220.0
EndpointKey = tuple[str, str]


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    """Translate shared, centre-origin coordinates into KiCad coordinates."""
    return pcbnew.VECTOR2I(
        pcbnew.FromMM(x + ORIGIN_X_MM), pcbnew.FromMM(ORIGIN_Y_MM - y)
    )


def add_trace(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    layer: int = pcbnew.F_Cu,
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


def add_via(board: pcbnew.BOARD, net: pcbnew.NETINFO_ITEM, at: pcbnew.VECTOR2I) -> None:
    """Add one standard through-via at an exact position."""
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(at)
    via.SetWidth(pcbnew.FromMM(rules.VIA_PAD_MM))
    via.SetDrill(pcbnew.FromMM(rules.VIA_DRILL_MM))
    via.SetNet(net)
    board.Add(via)


def _add_mounting_holes(board: pcbnew.BOARD) -> None:
    """Add one plated-copper-free screw clearance over every case boss."""
    shared = dimensions
    diameter = shared.PCB_MOUNTING_HOLE_DIAMETER_MM
    for index, (x, y) in enumerate(shared.PCB_SUPPORT_POSITIONS_MM, 1):
        module = pcbnew.FOOTPRINT(board)
        module.SetReference(f"H{index}")
        module.SetValue("M3 mounting hole")
        module.SetBoardOnly(True)
        module.SetExcludedFromBOM(True)
        module.SetExcludedFromPosFiles(True)
        module.Reference().SetVisible(False)
        module.Value().SetVisible(False)
        module.SetPosition(point(x, y))
        board.Add(module)
        pad = pcbnew.PAD(module)
        pad.SetNumber("")
        pad.SetPosition(point(x, y))
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        size = pcbnew.FromMM(diameter)
        pad.SetSize(pcbnew.VECTOR2I(size, size))
        pad.SetDrillSize(pcbnew.VECTOR2I(size, size))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetLayerSet(pad.UnplatedHoleMask())
        module.Add(pad)
        radius = diameter / 2 + 0.5
        corners = (
            (x - radius, y - radius),
            (x + radius, y - radius),
            (x + radius, y + radius),
            (x - radius, y + radius),
        )
        for corner_index, start in enumerate(corners):
            line = pcbnew.PCB_SHAPE(module)
            line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(point(*start))
            line.SetEnd(point(*corners[(corner_index + 1) % 4]))
            line.SetLayer(pcbnew.F_CrtYd)
            line.SetWidth(pcbnew.FromMM(rules.COURTYARD_LINE_MM))
            module.Add(line)


def _add_outline(board: pcbnew.BOARD) -> None:
    width, height, _ = dimensions.PCB_SIZE_MM
    x0, x1 = (-width / 2, width / 2)
    y1 = dimensions.PLAYING_SPAN_MM / 2
    y0 = y1 - height
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    for index, start in enumerate(corners):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(point(*start))
        edge.SetEnd(point(*corners[(index + 1) % 4]))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(rules.OUTLINE_LINE_MM))
        board.Add(edge)


def add_power_planes(board: pcbnew.BOARD) -> None:
    """Add inset ground, 5 V, and 3.3 V zones on dedicated internal layers."""
    edges = [
        item
        for item in board.GetDrawings()
        if isinstance(item, pcbnew.PCB_SHAPE) and item.GetLayer() == pcbnew.Edge_Cuts
    ]
    xs = [item.GetStart().x for item in edges]
    ys = [item.GetStart().y for item in edges]
    inset = pcbnew.FromMM(1.0)
    left, right, top, bottom = (
        min(xs) + inset,
        max(xs) - inset,
        min(ys) + inset,
        max(ys) - inset,
    )
    corners = ((left, bottom), (right, bottom), (right, top), (left, top))
    for name, layer in (
        (Net.GROUND, pcbnew.In1_Cu),
        (Net.FIVE_VOLTS, pcbnew.In2_Cu),
        (Net.THREE_VOLTS_THREE, pcbnew.In3_Cu),
    ):
        zone = pcbnew.ZONE(board)
        net = board.FindNet(name)
        if net is None:
            raise ValueError(f"missing power net {name}")
        zone.SetNet(net)
        zone.SetLayer(layer)
        zone.Outline().NewOutline()
        for x, y in corners:
            zone.Outline().Append(x, y)
        board.Add(zone)


def write_board(board: pcbnew.BOARD, board_path: Path, dsn_path: Path) -> None:
    """Fill zones, save the native board, and export its router interchange file."""
    pcbnew.SaveBoard(str(board_path), board)
    filled = pcbnew.LoadBoard(str(board_path))
    pcbnew.ZONE_FILLER(filled).Fill(filled.Zones())
    temporary = board_path.with_suffix(".filled.kicad_pcb")
    pcbnew.SaveBoard(str(temporary), filled)
    temporary.replace(board_path)
    temporary.with_suffix(".kicad_pro").unlink(missing_ok=True)
    identities = stable_uuid_map(filled)
    text = board_path.read_text()
    board_path.write_text(
        re.sub(
            '\\(uuid "([0-9a-f-]+)"\\)',
            lambda match: f'(uuid "{identities[match[1]]}")',
            text,
        )
    )
    filled = pcbnew.LoadBoard(str(board_path))
    dsn_path.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.ExportSpecctraDSN(filled, str(dsn_path)):
        raise RuntimeError("KiCad failed to export the autorouter design")
    lines = dsn_path.read_text().splitlines(keepends=True)
    if not lines or not lines[0].startswith('(pcb "'):
        raise RuntimeError("unexpected KiCad Specctra header")
    lines[0] = f'(pcb "{dsn_path.name}"\n'
    dsn_path.write_text("".join(lines))


def stable_uuid_map(board: pcbnew.BOARD) -> dict[str, str]:
    """Semantic identities survive insertion and ordering of unrelated objects.

    Exact duplicate geometric items use an occurrence counter scoped to that
    geometry only. Net codes and the global construction index are never keys.
    """
    identities: dict[str, str] = {}
    occurrences: Counter[str] = Counter()

    def identify(item: pcbnew.BOARD_ITEM, key: str) -> None:
        occurrence = occurrences[key]
        occurrences[key] += 1
        identities[item.m_Uuid.AsString()] = uid(f"pcb:{key}:{occurrence}")

    def shape_key(shape: pcbnew.PCB_SHAPE, origin: pcbnew.VECTOR2I) -> str:
        ends = sorted(
            (p.x - origin.x, p.y - origin.y) for p in (shape.GetStart(), shape.GetEnd())
        )
        return f"shape:{shape.GetLayer()}:{shape.GetShape()}:{ends}:{shape.GetWidth()}"

    for footprint in board.GetFootprints():
        key = f"footprint:{footprint.GetReference()}"
        identify(footprint, key)
        for field in footprint.GetFields():
            identify(field, f"{key}/field:{field.GetName()}")
        for pad in footprint.Pads():
            identify(pad, f"{key}/pad:{pad.GetNumber()}")
        for shape in footprint.GraphicalItems():
            identify(shape, f"{key}/{shape_key(shape, footprint.GetPosition())}")
    for track in board.GetTracks():
        ends = sorted((p.x, p.y) for p in (track.GetStart(), track.GetEnd()))
        if isinstance(track, pcbnew.PCB_VIA):
            key = f"via:{track.GetNetname()}:{ends}:{track.GetWidth(pcbnew.F_Cu)}:{track.GetDrillValue()}"
        else:
            key = f"track:{track.GetNetname()}:{track.GetLayer()}:{ends}:{track.GetWidth()}"
        identify(track, key)
    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_TEXT):
            at = drawing.GetPosition()
            key = f"text:{drawing.GetLayer()}:{drawing.GetText()}:{at.x}:{at.y}"
        elif isinstance(drawing, pcbnew.PCB_SHAPE):
            key = shape_key(drawing, pcbnew.VECTOR2I(0, 0))
        else:
            raise ValueError("unsupported native drawing identity")
        identify(drawing, key)
    for zone in board.Zones():
        identify(zone, f"plane:{zone.GetNetname()}:{zone.GetLayer()}")
    return identities


def new_board() -> pcbnew.BOARD:
    pcbnew.KIID.SeedGenerator(0x43484553)
    board = pcbnew.BOARD()
    title = board.GetTitleBlock()
    title.SetTitle("Chess Smart Board - Single Board Electronics")
    title.SetRevision("D-PROTOTYPE")
    board.SetTitleBlock(title)
    board.SetCopperLayerCount(rules.COPPER_LAYERS)
    settings = board.GetDesignSettings()
    settings.SetBoardThickness(pcbnew.FromMM(dimensions.PCB_THICKNESS_MM))
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
    return board


def parts(board: pcbnew.BOARD) -> list[pcbnew.FOOTPRINT]:
    """The purchased assemblies, excluding board-only mounting holes."""
    return sorted(
        (f for f in board.GetFootprints() if f.HasFieldByName("PartKey")),
        key=lambda f: f.GetReference(),
    )


def place[Part: EndpointResolver](
    board: pcbnew.BOARD,
    model: Part,
    *,
    part_key: str,
    at: tuple[float, float],
    assembly: str,
    library: str,
    value: str,
    description: str,
    rotation: float = 0.0,
    extras: dict[str, str] | None = None,
) -> Part:
    """Install an approved native template; return only its shared logical ports."""
    if board.FindFootprintByReference(model.reference) is not None:
        raise ValueError(f"duplicate reference: {model.reference}")
    if not isinstance(model, type(MODELS[part_key](model.reference))):
        raise ValueError(f"{model.reference}: incompatible approved product")
    spec = COMPONENTS[part_key]
    template = TEMPLATES[part_key]
    module = template.Duplicate()
    # KiCad's copy constructor normalizes non-square circular PTH land sizes.
    # Restore the approved native dimensions before placing the duplicate.
    sizes = {p.GetNumber(): p.GetSize() for p in template.Pads()}
    for pad in module.Pads():
        pad.SetSize(sizes[pad.GetNumber()])
    module.SetReference(model.reference)
    module.SetValue(spec.mpn)
    module.SetLibDescription(f"{spec.manufacturer} {spec.mpn}: {spec.description}")
    for key, text in {
        "PartKey": part_key,
        "Assembly": assembly,
        "Library": library,
        "NominalValue": value,
        "Purpose": description,
        **(extras or {}),
    }.items():
        module.SetField(key, text)
    for field in module.GetFields():
        field.SetVisible(False)
    sheet = assembly
    if assembly.startswith("square/"):
        bank, _ = wiring.expander_of(*wiring.parse_square(assembly.split("/")[1]))
        sheet = "bank-" + dimensions.HALL_BANKS[bank].label
    elif assembly.startswith("sensing/"):
        sheet = "bank-" + assembly.split("/")[1]
    module.SetPath(
        pcbnew.KIID_PATH(
            f"/{ROOT_UUID}/{uid('sheet:' + sheet)}/{uid('symbol:' + model.reference)}"
        )
    )
    module.SetPosition(point(*at))
    module.SetOrientationDegrees(rotation)
    # Keep pad axes global when rotating footprints, including oblong drills.
    for pad in module.Pads():
        if rotation % 180 == 90:
            size, drill, shape = pad.GetSize(), pad.GetDrillSize(), pad.GetShape()
            pad.SetShape(pcbnew.PAD_SHAPE_RECT)
            pad.SetSize(pcbnew.VECTOR2I(size.y, size.x))
            pad.SetDrillSize(pcbnew.VECTOR2I(drill.y, drill.x))
            pad.SetShape(shape)
        pad.SetOrientationDegrees(0)
    # Convert every item from the same centre-origin position so rounding stays
    # consistent across the footprint.
    origin = module.GetPosition()

    def located(at_native: pcbnew.VECTOR2I) -> pcbnew.VECTOR2I:
        return point(
            at[0] + round(pcbnew.ToMM(at_native.x - origin.x), 4),
            at[1] - round(pcbnew.ToMM(at_native.y - origin.y), 4),
        )

    for pad in module.Pads():
        pad.SetPosition(located(pad.GetPosition()))
    for shape in module.GraphicalItems():
        shape.SetStart(located(shape.GetStart()))
        shape.SetEnd(located(shape.GetEnd()))
    board.Add(module)
    return model


def logical_pin(pad: pcbnew.PAD) -> str:
    """Bind each duplicate four-leg switch contact to its logical pin."""
    return {"1b": "1", "2b": "2"}.get(pad.GetNumber(), pad.GetNumber())


def connect(board: pcbnew.BOARD, name: str, *pins: BoundPin) -> None:
    """Assign native pads from component-bound datasheet pins; reject reassignment."""
    if not name or not pins:
        raise ValueError("a connection requires a name and pins")
    selected: list[pcbnew.PAD] = []
    for pin in pins:
        reference, number = pin.endpoint
        module = board.FindFootprintByReference(reference)
        if module is None:
            raise ValueError(f"unplaced component: {reference}")
        pads = [p for p in module.Pads() if logical_pin(p) == number]
        if not pads or any(p.GetNetCode() != 0 for p in pads):
            raise ValueError(f"{reference}/{number}: unknown or already connected pin")
        selected.extend(pads)
    if len({p.m_Uuid.AsString() for p in selected}) != len(selected):
        raise ValueError("repeated pin in connection")
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name, board.GetNetCount())
        board.Add(net)
    for pad in selected:
        pad.SetNet(net)


def no_connect(board: pcbnew.BOARD, pin: BoundPin) -> None:
    reference, number = pin.endpoint
    connect(board, f"unconnected-({reference}-Pad{number})", pin)


def endpoint_pads(board: pcbnew.BOARD) -> dict[EndpointKey, pcbnew.PAD]:
    return {
        (f.GetReference(), logical_pin(p)): p for f in parts(board) for p in f.Pads()
    }


def connections(board: pcbnew.BOARD) -> dict[str, tuple[EndpointKey, ...]]:
    """A sorted view of actual native pad assignments, never an input graph."""
    found: defaultdict[str, set[EndpointKey]] = defaultdict(set)
    for endpoint, pad in endpoint_pads(board).items():
        found[pad.GetNetname()].add(endpoint)
    return {name: tuple(sorted(endpoints)) for name, endpoints in sorted(found.items())}


def add_mechanical_features(board: pcbnew.BOARD) -> None:
    from pcb.definition.output.markings import add_front_silkscreen, add_square_grid

    _add_outline(board)
    _add_mounting_holes(board)
    add_square_grid(board)
    add_front_silkscreen(board)
