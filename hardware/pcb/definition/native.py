"""Native board authoring, checked logical-pin assignment, and KiCad serialization.

Role: the thin layer between this repo's typed part/pin contracts and KiCad's
`pcbnew` API. Assemblies call `place()` to install an approved footprint and
`connect()` to assign pads to nets; `new_board()` configures design rules from
`rules.py`; `write_board()` saves the board, fills copper zones and exports the
Specctra DSN (exported for optional external-router use or review; the
build itself does not consume it). There is deliberately no second model of the
board: connectivity is read back from the pads themselves (`connections()`).

Coordinate convention: callers use shared board millimetres (origin at the playing
area centre, Y up). KiCad uses an absolute page position with Y down, so `point()`
is the only place that converts.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew

from pcb.definition import rules
from pcb.definition.output.symbols import ROOT_UUID, uid
from pcb.definition.parts.part import DrawingView, PcbPart
from pcb.definition.rules import Net
from shared import dimensions, wiring
from shared.electronics import BoundPin, Endpoint, EndpointResolver

# Where the board's centre-origin (0, 0) lands on KiCad's page. The values are
# arbitrary but must stay fixed: they place the board inside the page and feed the
# geometry-derived UUIDs, so changing them moves everything in the generated files.
ORIGIN_X_MM = 200.0
ORIGIN_Y_MM = 220.0


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    """Translate shared, centre-origin coordinates into KiCad coordinates.

    Adds the page origin and flips Y (shared Y is up, KiCad Y is down).
    """
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
    """Add one exact point-to-point copper segment.

    Used by routing code once it has chosen a path; no clearance checking happens
    here (DRC does that), and `layer` is a pcbnew layer id.
    """
    trace = pcbnew.PCB_TRACK(board)
    trace.SetStart(start)
    trace.SetEnd(end)
    trace.SetWidth(pcbnew.FromMM(width))
    trace.SetLayer(layer)
    trace.SetNet(net)
    board.Add(trace)


def add_via(board: pcbnew.BOARD, net: pcbnew.NETINFO_ITEM, at: pcbnew.VECTOR2I) -> None:
    """Add one standard through-via at an exact position.

    Size comes from `rules` so every via is the same, matching the minimum via size
    configured in `new_board()`.
    """
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(at)
    via.SetWidth(pcbnew.FromMM(rules.VIA_PAD_MM))
    via.SetDrill(pcbnew.FromMM(rules.VIA_DRILL_MM))
    via.SetNet(net)
    board.Add(via)


def _add_mounting_holes(board: pcbnew.BOARD) -> None:
    """Add one plated-copper-free screw clearance over every case boss.

    Positions come from the shared case dimensions so the PCB holes line up with
    the enclosure supports. Each hole is a non-plated (NPTH) pad with no copper, plus
    a courtyard square slightly larger than the hole to keep parts away from it. The
    footprint is board-only: not in the BOM or the pick-and-place file.
    """
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
    """Draw the rectangular board edge on Edge_Cuts.

    The rectangle spans the playing area plus the front control strip: its top edge
    is the playing area's top, and it extends downward by the full PCB height.
    """
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
    """Add inset ground, 5 V, 3.3 V and LED 5 V zones on dedicated internal layers.

    One full-board plane per rail (GND on In1, +5V on In2, +3V3 on In3, the switched
    LED_5V on In6 since S6), inset 1 mm
    from the outline so copper stays clear of the edge. Planes give power and ground
    low-impedance distribution; signals route on the remaining layers. Zones are
    only outlines here: `write_board()` fills them.
    """
    # Derive the inset rectangle from the drawn outline, not from dimensions, so the
    # planes always follow whatever outline was actually added.
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
        (Net.LED_FIVE_VOLTS, pcbnew.In6_Cu),
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
    """Fill zones, save the native board, and export its router interchange file.

    Steps: save; reload and fill copper zones; save again; rewrite KiCad-assigned
    UUIDs to the stable semantic ones from `stable_uuid_map`; export the Specctra
    DSN, which the build itself does not consume.
    The temporary `.kicad_pro` KiCad writes beside the filled copy is deleted.
    """
    pcbnew.SaveBoard(str(board_path), board)
    # Fill zones on a reloaded copy, then replace the saved file with it.
    filled = pcbnew.LoadBoard(str(board_path))
    pcbnew.ZONE_FILLER(filled).Fill(filled.Zones())
    temporary = board_path.with_suffix(".filled.kicad_pcb")
    pcbnew.SaveBoard(str(temporary), filled)
    temporary.replace(board_path)
    temporary.with_suffix(".kicad_pro").unlink(missing_ok=True)
    # Replace every `(uuid "...")` token with its deterministic equivalent so the
    # saved file is reproducible and diffs show only real design changes.
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
    # The DSN is exported for optional external-router use or review only.
    if not pcbnew.ExportSpecctraDSN(filled, str(dsn_path)):
        raise RuntimeError("KiCad failed to export the autorouter design")
    lines = dsn_path.read_text().splitlines(keepends=True)
    if not lines or not lines[0].startswith('(pcb "'):
        raise RuntimeError("unexpected KiCad Specctra header")
    # Normalize the header to the DSN's own file name so the output does not depend
    # on whatever name KiCad wrote there.
    lines[0] = f'(pcb "{dsn_path.name}"\n'
    dsn_path.write_text("".join(lines))


def stable_uuid_map(board: pcbnew.BOARD) -> dict[str, str]:
    """Map each item's random KiCad UUID to a deterministic, meaning-derived one.

    Semantic identities survive insertion and ordering of unrelated objects.

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
    """Create an empty board with title, stackup size and all design rules applied.

    Rule values come from `rules.py`, so KiCad's own DRC enforces the same limits
    the router and `validate()` assume.
    """
    # Fix the random generator so any UUIDs KiCad assigns are reproducible run to
    # run (the seed spells "CHES").
    pcbnew.KIID.SeedGenerator(0x43484553)
    board = pcbnew.BOARD()
    title = board.GetTitleBlock()
    title.SetTitle("Chess Smart Board - Single Board Electronics")
    title.SetRevision("D-PROTOTYPE")
    board.SetTitleBlock(title)
    board.SetCopperLayerCount(rules.COPPER_LAYERS)
    settings = board.GetDesignSettings()
    settings.SetBoardThickness(pcbnew.FromMM(dimensions.PCB_THICKNESS_MM))
    # Board floors sit at the U74 exception; the generated .kicad_dru and the
    # netclass keep CLEARANCE_MM / TRACE_WIDTH_MM everywhere else.
    settings.m_MinClearance = pcbnew.FromMM(rules.FINE_PITCH_CLEARANCE_MM)
    settings.m_TrackMinWidth = pcbnew.FromMM(rules.FINE_PITCH_TRACE_WIDTH_MM)
    settings.m_HoleClearance = pcbnew.FromMM(rules.HOLE_CLEARANCE_MM)
    settings.m_HoleToHoleMin = pcbnew.FromMM(rules.HOLE_TO_HOLE_MM)
    settings.m_CopperEdgeClearance = pcbnew.FromMM(rules.POUR_TO_OUTLINE_MM)
    settings.m_ViasMinSize = pcbnew.FromMM(rules.VIA_PAD_MM)
    settings.m_ViasMinAnnularWidth = pcbnew.FromMM(
        rules.annular_ring(rules.VIA_PAD_MM, rules.VIA_DRILL_MM)
    )
    settings.m_MinThroughDrill = pcbnew.FromMM(rules.PCBWAY_MIN_DRILL_MM)
    # Mask dam and silk spacing use the fabricator minimum (deliberately set at the fab minimum).
    settings.m_SilkClearance = pcbnew.FromMM(rules.PCBWAY_MIN_MASK_DAM_MM)
    settings.m_SolderMaskMinWidth = pcbnew.FromMM(rules.PCBWAY_MIN_MASK_DAM_MM)
    return board


def parts(board: pcbnew.BOARD) -> list[pcbnew.FOOTPRINT]:
    """The purchased assemblies, excluding board-only mounting holes.

    Identified by the `PartKey` field that `place()` sets; sorted by reference so
    every output (BOM, netlist) lists parts in a stable order.
    """
    return sorted(
        (f for f in board.GetFootprints() if f.HasFieldByName("PartKey")),
        key=lambda f: f.GetReference(),
    )


def place[Part: EndpointResolver](
    board: pcbnew.BOARD,
    part: PcbPart[Part],
    reference: str,
    *,
    at: tuple[float, float],
    assembly: str,
    rotation: float = 0.0,
    purpose: str | None = None,
    nominal_value: str | None = None,
    extras: dict[str, str] | None = None,
    bottom: bool = False,
) -> Part:
    """Install an approved native template; return only its shared logical ports.

    `part` binds an approved product to its native footprint template; `reference`
    is the explicit, stable designator; `at` is the centre in shared mm and `rotation`
    degrees. The footprint records its product key, assembly, library label, nominal
    value, purpose and any `extras` as hidden fields: BOM, netlist and schematic are
    built from those, so this is where design intent enters the board. Pads start
    unassigned; callers must `connect()` or `no_connect()` every pin. The returned
    model exposes pins by datasheet role, not by pad number.
    """
    if board.FindFootprintByReference(reference) is not None:
        raise ValueError(f"duplicate reference: {reference}")
    model = part.new_model(reference)
    spec = part.spec
    template = part.template
    # Copy the shared template so each placement owns independent pads and fields.
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
        "PartKey": spec.key,
        "Assembly": assembly,
        "Library": part.library,
        "NominalValue": nominal_value or part.nominal_value,
        "Purpose": purpose or part.default_purpose,
        **(extras or {}),
    }.items():
        module.SetField(key, text)
    for field in module.GetFields():
        field.SetVisible(False)
    # Link the footprint to its generated schematic symbol (by deterministic UUID
    # path) so KiCad's schematic/PCB parity check sees them as the same part. Squares
    # are drawn on their Hall bank's sheet, hence the bank lookup.
    sheet = assembly
    if assembly.startswith("square/"):
        channel = wiring.expander_of(wiring.parse_square(assembly.split("/")[1]))
        sheet = "bank-" + channel.bank.label
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
    if bottom:
        _move_to_bottom(module, part.drawing_view)
    return model


# Pad shapes that look the same mirrored or turned 180 degrees about their centre.
MIRROR_SAFE_PAD_SHAPES = frozenset(
    {pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_OVAL}
)


def _move_to_bottom(module: pcbnew.FOOTPRINT, view: DrawingView) -> None:
    """Put a through-hole part on the back side as its drawing view requires.

    A mounting-side drawing (the datasheet layout seen from the part) is mirrored by
    KiCad's flip exactly as the physical part is when it moves underneath. A
    board-top drawing (holes fixed by a mating part seen from the top) must keep its
    positions, so every pad and drawing is moved back after the flip.
    """
    if any(pad.GetAttribute() != pcbnew.PAD_ATTRIB_PTH for pad in module.Pads()):
        raise ValueError(
            f"{module.GetReference()}: only through-hole parts go on the bottom"
        )
    if any(pad.GetShape() not in MIRROR_SAFE_PAD_SHAPES for pad in module.Pads()):
        raise ValueError(f"{module.GetReference()}: pad shape is not mirror-safe")

    # Copy the coordinates: SWIG returns live references that the flip rewrites.
    def copied(point: pcbnew.VECTOR2I) -> pcbnew.VECTOR2I:
        return pcbnew.VECTOR2I(point.x, point.y)

    sizes = [
        (pad, copied(pad.GetSize()), copied(pad.GetDrillSize()))
        for pad in module.Pads()
    ]
    pads = [(pad, copied(pad.GetPosition())) for pad in module.Pads()]
    shapes = [
        (shape, copied(shape.GetStart()), copied(shape.GetEnd()))
        for shape in module.GraphicalItems()
    ]
    module.Flip(module.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    if view is DrawingView.BOARD_TOP:
        for pad, at in pads:
            pad.SetPosition(at)
        for shape, start, end in shapes:
            shape.SetStart(start)
            shape.SetEnd(end)
    # Pads keep their global axes (place() already swapped sizes for 90 degrees).
    for pad, size, drill in sizes:
        pad.SetOrientationDegrees(0)
        if pad.GetSize() != size or pad.GetDrillSize() != drill:
            raise ValueError(f"{module.GetReference()}: pad axes changed in the flip")


def logical_pin(pad: pcbnew.PAD) -> str:
    """Bind each duplicate four-leg switch contact to its logical pin.

    The tactile switch footprint has two pads per contact ("1" and "1b"); both are
    the same electrical pin, so "1b"/"2b" map back to "1"/"2" and are always
    assigned to the same net together.
    """
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


def endpoint_pads(board: pcbnew.BOARD) -> dict[Endpoint[str], pcbnew.PAD]:
    return {
        Endpoint(f.GetReference(), logical_pin(p)): p
        for f in parts(board)
        for p in f.Pads()
    }


def connections(board: pcbnew.BOARD) -> dict[str, tuple[Endpoint[str], ...]]:
    """A sorted view of actual native pad assignments, never an input graph."""
    found: defaultdict[str, set[Endpoint[str]]] = defaultdict(set)
    for endpoint, pad in endpoint_pads(board).items():
        found[pad.GetNetname()].add(endpoint)
    return {name: tuple(sorted(endpoints)) for name, endpoints in sorted(found.items())}


def add_mechanical_features(board: pcbnew.BOARD) -> None:
    from pcb.definition.output.markings import add_front_silkscreen, add_square_grid

    _add_outline(board)
    _add_mounting_holes(board)
    add_square_grid(board)
    add_front_silkscreen(board)
