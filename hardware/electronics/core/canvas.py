"""Schemdraw canvas: place components, wire nets, save SVG and PNG."""

from __future__ import annotations

import os
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

_CACHE = Path(__file__).resolve().parents[2] / ".cache" / "matplotlib"
_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")
# Element ids are hashed from this salt. Without a fixed one they change every
# run, and a committed drawing would show as modified after every build.
matplotlib.rcParams["svg.hashsalt"] = "chess-electronics"

import schemdraw
from schemdraw import elements as elm

from components import Component

NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://chess.local/electronics")

# Schemdraw sizes geometry in drawing units but text in points, so these two
# numbers set how crowded the sheet looks. Shrinking inches_per_unit is what
# makes a drawing feel compressed: the circuit gets smaller while every label
# stays the same size. Keep the geometry generous and the type small.
UNIT = 3.0
INCHES_PER_UNIT = 0.55
BASE_FONT = 9
REFERENCE_FONT = 9
VALUE_FONT = 8
NET_FONT = 8
TITLE_SIZE = 15
LABEL_SIZE = 10
PNG_DPI = int(os.environ.get("ELECTRONICS_PNG_DPI", "150"))
PNG_MAX_PIXELS = int(os.environ.get("ELECTRONICS_PNG_MAX_PIXELS", "5000"))
STUB = 1.3
GROUNDS = {"GND"}
SUPPLIES = {"+5V", "+3V3"}

# Drawing furniture: section outlines, sheet border, title block.
RULE_COLOR = "#3c4043"
SECTION_COLOR = "#9aa0a6"
SECTION_FILL = "#fbfbfc"
SECTION_PAD = 1.8
SECTION_TITLE_FONT = 10
FRAME_MARGIN = 2.4
TITLE_BLOCK_WIDTH = 30.0
TITLE_BLOCK_HEIGHT = 7.5
FIELD_FONT = 7.5
FIELD_VALUE_FONT = 9.0


def uid(*parts: object) -> str:
    return str(uuid.uuid5(NS, ":".join(str(part) for part in parts)))


def _pt(x: float, y: float) -> tuple[float, float]:
    return (round(x, 2), round(y, 2))


@dataclass
class SheetInfo:
    title: str
    project: str
    comments: tuple[str, ...] = ()
    rev: str = "A-PROTOTYPE"
    date: str = "2026-03-12"
    sheet: str = "1/1"


@dataclass
class SymbolSpec:
    lib: str
    reference: str
    x: float
    y: float
    value: str
    package: str = ""
    description: str = ""
    ordering: str = ""
    extras: dict[str, str] = field(default_factory=dict)


class Schematic:
    def __init__(self, info: SheetInfo) -> None:
        self.info = info
        self.drawing = schemdraw.Drawing(show=False)
        self.drawing.config(
            unit=UNIT,
            inches_per_unit=INCHES_PER_UNIT,
            fontsize=BASE_FONT,
            lw=1.4,
            bgcolor="white",
        )
        self.symbols: list[SymbolSpec] = []
        self.placed: dict[str, tuple[elm.Element, dict[str, str]]] = {}
        self.labels: list[str] = []
        self._parent: dict[tuple[float, float], tuple[float, float]] = {}
        self._pins: dict[tuple[float, float], set[tuple[str, str]]] = {}
        self._names: dict[tuple[float, float], str] = {}
        # Drawn segments and the junction dots placed on them. A tap partway
        # along a rail is a connection, but `wire` only joins its own ends, so
        # the two have to be reconciled when the netlist is read out.
        self._segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
        self._taps: list[tuple[float, float]] = []

    def _add_point(self, x: float, y: float) -> tuple[float, float]:
        key = _pt(x, y)
        self._parent.setdefault(key, key)
        return key

    def _find(self, key: tuple[float, float]) -> tuple[float, float]:
        while self._parent[key] != key:
            self._parent[key] = self._parent[self._parent[key]]
            key = self._parent[key]
        return key

    def _union(self, a: tuple[float, float], b: tuple[float, float]) -> None:
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            self._parent[rb] = ra

    def _anchor(self, reference: str, number: str) -> str:
        _element, pin_map = self.placed[reference]
        return pin_map.get(number, number)

    def pin(self, reference: str, number: str) -> tuple[float, float]:
        element, _pin_map = self.placed[reference]
        point = element.absanchors[self._anchor(reference, number)]
        return (float(point.x), float(point.y))

    def place(
        self,
        part: Component,
        reference: str,
        x: float,
        y: float,
        extras: dict[str, str] | None = None,
        visible_extras: set[str] | None = None,
    ) -> None:
        extra_items = extras or {}
        visible = visible_extras or set()
        element = part.build()
        element.at((x, y))
        # The square name rides along with the reference; as a separate label it
        # lands on the cell's own wiring.
        square = extra_items.get("Square") if "Square" in visible else None
        caption = f"{reference}  {square}" if square else reference
        if part.pins:
            element.label(caption, loc="top", fontsize=REFERENCE_FONT)
            element.label(part.value, loc="bottom", fontsize=VALUE_FONT)
        else:
            # Integrated circuits label themselves underneath and may carry a pin
            # on top, so their reference sits off to the upper left.
            element.label(
                caption,
                loc="top",
                ofst=(-1.6, 0.0),
                halign="right",
                fontsize=REFERENCE_FONT,
            )
        self.drawing.add(element)
        self.placed[reference] = (element, part.pins)
        self.symbols.append(
            SymbolSpec(
                part.lib,
                reference,
                x,
                y,
                part.value,
                part.package,
                part.description,
                part.ordering,
                extra_items,
            )
        )
        numbers = list(part.pins) or [
            name for name in element.absanchors if name.isdigit()
        ]
        for number in numbers:
            px, py = self.pin(reference, number)
            self._pins.setdefault(self._add_point(px, py), set()).add((reference, number))

    def wire(self, x1: float, y1: float, x2: float, y2: float) -> None:
        if (x1, y1) == (x2, y2):
            return
        if x1 != x2 and y1 != y2:
            self.wire(x1, y1, x2, y1)
            self.wire(x2, y1, x2, y2)
            return
        self.drawing.add(elm.Line().at((x1, y1)).to((x2, y2)))
        start, end = self._add_point(x1, y1), self._add_point(x2, y2)
        self._segments.append((start, end))
        self._union(start, end)

    def tap(self, x: float, y: float) -> None:
        self.drawing.add(elm.Dot().at((x, y)))
        self._taps.append(self._add_point(x, y))

    def hv(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.wire(x1, y1, x2, y1)
        self.wire(x2, y1, x2, y2)

    def vh(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.wire(x1, y1, x1, y2)
        self.wire(x1, y2, x2, y2)

    def _flag(self, net: str, x: float, y: float, pointing_right: bool) -> None:
        """Rail symbol for supplies and grounds, a name flag for signals.

        A rotated Tag stretches into an unreadable pill, so vertical rails use
        the conventional supply and ground symbols instead.
        """
        if net in GROUNDS:
            self.drawing.add(elm.Ground().at((x, y)))
        elif net in SUPPLIES:
            self.drawing.add(elm.Vdd().at((x, y)).label(net, fontsize=NET_FONT))
        else:
            tag = elm.Tag().right() if pointing_right else elm.Tag().left()
            self.drawing.add(tag.label(net, fontsize=NET_FONT).at((x, y)))
        self.labels.append(net)
        self._names[self._add_point(x, y)] = net

    def label(self, name: str, x: float, y: float, rotation: int = 0) -> None:
        del rotation
        self._flag(name, x, y, pointing_right=True)

    def label_pin(self, net: str, ref: str, number: str) -> None:
        """Stub the pin clear of the body, then flag the stub end."""
        x, y = self.pin(ref, number)
        element, _pin_map = self.placed[ref]
        center = element.absanchors.get("center", element.absanchors["xy"])
        dx = float(x) - float(center.x)
        dy = float(y) - float(center.y)
        if abs(dx) >= abs(dy):
            end = (x + (STUB if dx >= 0 else -STUB), y)
        else:
            end = (x, y + (STUB if dy >= 0 else -STUB))
        self.wire(x, y, *end)
        self._flag(net, *end, pointing_right=dx >= 0)

    def nc(self, x: float, y: float) -> None:
        self.drawing.add(elm.NoConnect().at((x, y)))

    def text(
        self, body: str, x: float, y: float, size: float = TITLE_SIZE, *, bold: bool = True
    ) -> None:
        del bold
        self._caption(body, x, y, size)
        self.labels.append(body)

    def note(self, body: str, x: float, y: float) -> None:
        """An engineering note, set quieter than the circuit it explains."""
        self._caption(body, x, y, LABEL_SIZE, color=RULE_COLOR)
        self.labels.append(body)

    @contextmanager
    def section(self, title: str) -> Iterator[None]:
        """Outline and title whatever gets drawn inside the block.

        Measuring the elements afterwards keeps the outline honest: it can
        never drift out of step with a layout change the way a hand-placed
        rectangle would.
        """
        first = len(self.drawing.elements)
        yield
        bounds = self._bounds(self.drawing.elements[first:])
        if bounds is None:
            return
        x0, y0, x1, y1 = bounds
        self._outline(
            x0 - SECTION_PAD,
            y0 - SECTION_PAD,
            x1 + SECTION_PAD,
            y1 + SECTION_PAD,
            SECTION_COLOR,
            0.9,
            fill=SECTION_FILL,
        )
        self._caption(
            title.upper(),
            x0 - SECTION_PAD,
            y1 + SECTION_PAD + 0.7,
            SECTION_TITLE_FONT,
            color=RULE_COLOR,
        )

    @staticmethod
    def _bounds(elements) -> tuple[float, float, float, float] | None:
        boxes = []
        for element in elements:
            try:
                boxes.append(element.get_bbox(transform=True))
            except Exception:  # noqa: BLE001 - furniture must never break a build
                continue
        if not boxes:
            return None
        return (
            min(b.xmin for b in boxes),
            min(b.ymin for b in boxes),
            max(b.xmax for b in boxes),
            max(b.ymax for b in boxes),
        )

    def _outline(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        color: str,
        width: float,
        fill: str | None = None,
    ) -> None:
        rect = elm.Rect(corner1=(x0, y0), corner2=(x1, y1), fill=fill)
        self.drawing.add(
            rect.at((0, 0)).right().color(color).linewidth(width).zorder(0)
        )

    def _rule(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.drawing.add(
            elm.Line().at((x0, y0)).to((x1, y1)).color(RULE_COLOR).linewidth(0.9)
        )

    def _caption(
        self,
        body: str,
        x: float,
        y: float,
        size: float,
        color: str = "black",
        valign: str = "bottom",
    ) -> None:
        self.drawing.add(
            elm.Label()
            .at((x, y))
            .right()
            .color(color)
            .label(body, fontsize=size, halign="left", valign=valign)
        )

    def _field(self, name: str, value: str, x: float, y: float) -> None:
        self._caption(name.upper(), x, y + 1.2, FIELD_FONT, color=SECTION_COLOR)
        self._caption(value, x, y, FIELD_VALUE_FONT)

    def _title_block(self, x1: float, y0: float, width: float, height: float) -> None:
        """Standard lower-right title block: heading over a row of fields."""
        x0 = x1 - width
        y1 = y0 + height
        split = y0 + height * 0.42
        thirds = [x0 + width * 0.40, x0 + width * 0.68]
        self._outline(x0, y0, x1, y1, RULE_COLOR, 1.4)
        self._rule(x0, split, x1, split)
        for x in thirds:
            self._rule(x, y0, x, split)

        info = self.info
        self._caption(info.title, x0 + 1.0, split + height * 0.30, 12)
        note = info.comments[0] if info.comments else ""
        self._caption(note, x0 + 1.0, split + 0.7, FIELD_FONT, color=SECTION_COLOR)
        self._field("Project", info.project, x0 + 1.0, y0 + 0.9)
        self._field("Revision", info.rev, thirds[0] + 1.0, y0 + 0.9)
        self._field("Sheet", f"{info.sheet}   {info.date}", thirds[1] + 1.0, y0 + 0.9)

    def _add_frame(self) -> None:
        bounds = self._bounds(self.drawing.elements)
        if bounds is None:
            return
        x0, y0, x1, y1 = bounds
        # A title block is a small corner of a sheet, so size it against the
        # drawing rather than pinning it to one absolute width.
        width = min(max((x1 - x0) * 0.34, TITLE_BLOCK_WIDTH), TITLE_BLOCK_WIDTH * 2.2)
        height = min(max(width * 0.24, TITLE_BLOCK_HEIGHT), TITLE_BLOCK_HEIGHT * 1.6)
        left = x0 - FRAME_MARGIN
        right = max(x1 + FRAME_MARGIN, left + width + 2 * FRAME_MARGIN)
        block_top = y0 - FRAME_MARGIN
        bottom = block_top - height - FRAME_MARGIN
        self._title_block(right - FRAME_MARGIN, block_top - height, width, height)
        self._outline(left, bottom, right, y1 + FRAME_MARGIN, RULE_COLOR, 1.6)

    def _join_taps(self) -> None:
        """Join each junction dot to whatever segment runs through it.

        A dot partway along a rail is the drawing's way of saying "connected
        here". Only an explicit tap counts: two wires crossing without a dot are
        not joined, which is the same convention a reader applies by eye.
        """
        for tap in self._taps:
            for start, end in self._segments:
                if _on_segment(tap, start, end):
                    self._union(start, tap)

    def groups(self) -> list[set[tuple[str, str]]]:
        """Every electrically joined set of pins, named or not.

        A link drawn as a plain wire carries no net name, so it is invisible to
        `nets`. Continuity checks need to see it, which is what this exposes.
        """
        self._join_taps()
        grouped: dict[tuple[float, float], set[tuple[str, str]]] = {}
        for key, pins in self._pins.items():
            grouped.setdefault(self._find(key), set()).update(pins)
        return list(grouped.values())

    def equivalence(self) -> dict[tuple[str, str], int]:
        """Pin to circuit id, joining pins by drawn wire and by shared net name.

        Both mean the same thing on a schematic: a wire joins two pins, and so
        does giving two pins the same net label. Continuity checks have to
        respect both or a chain drawn partly with wires and partly with labels
        reads as broken when it is not.
        """
        circuit: dict[tuple[str, str], int] = {}
        merge: dict[int, int] = {}

        def root(node: int) -> int:
            while merge[node] != node:
                merge[node] = merge[merge[node]]
                node = merge[node]
            return node

        def union(a: int, b: int) -> None:
            ra, rb = root(a), root(b)
            if ra != rb:
                merge[rb] = ra

        for index, group in enumerate(self.groups()):
            merge[index] = index
            for pin in group:
                circuit[pin] = index
        for pins in self.nets().values():
            known = [circuit[pin] for pin in pins if pin in circuit]
            for other in known[1:]:
                union(known[0], other)
        return {pin: root(index) for pin, index in circuit.items()}

    def connected(self, a: tuple[str, str], b: tuple[str, str]) -> bool:
        circuits = self.equivalence()
        if a not in circuits or b not in circuits:
            return False
        return circuits[a] == circuits[b]

    def nets(self) -> dict[str, set[tuple[str, str]]]:
        self._join_taps()
        grouped: dict[tuple[float, float], set[tuple[str, str]]] = {}
        for key, pins in self._pins.items():
            grouped.setdefault(self._find(key), set()).update(pins)
        named = {self._find(key): name for key, name in self._names.items()}
        nets: dict[str, set[tuple[str, str]]] = {}
        for root, pins in grouped.items():
            name = named.get(root)
            if name is not None:
                nets.setdefault(name, set()).update(pins)
        return nets

    def net_of(self, ref: str, pin: str) -> str:
        hits = [name for name, nodes in self.nets().items() if (ref, pin) in nodes]
        if len(hits) != 1:
            raise AssertionError(f"{ref} pin {pin} nets={hits}")
        return hits[0]

    def save(self, directory: Path, name: str | None = None) -> Path:
        """Write this sheet's pair of renders; other sheets share the folder."""
        directory.mkdir(parents=True, exist_ok=True)
        stem = name or self.info.project
        self._add_frame()
        svg = directory / f"{stem}.svg"
        png = directory / f"{stem}.png"
        self.drawing.save(str(svg))
        svg.write_text(self._normalise(svg.read_text()))
        self.drawing.save(str(png), transparent=False, dpi=self._png_dpi())
        print(f"wrote {svg} and {png}")
        return svg

    def _normalise(self, svg: str) -> str:
        """Make a rebuilt drawing byte-identical when nothing has changed.

        Matplotlib stamps the current time into the metadata, and it breaks path
        data across lines with a trailing space on each, which the repository's
        whitespace check rejects.
        """
        svg = re.sub(
            r"<dc:date>[^<]*</dc:date>", f"<dc:date>{self.info.date}</dc:date>", svg
        )
        return "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"

    def _png_dpi(self) -> float:
        """Keep the screenshot openable; the SVG is the zoomable master."""
        bbox = self.drawing.get_bbox()
        longest = max(bbox.xmax - bbox.xmin, bbox.ymax - bbox.ymin) * INCHES_PER_UNIT
        if longest <= 0:
            return PNG_DPI
        return min(PNG_DPI, PNG_MAX_PIXELS / longest)


def _on_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    tolerance: float = 0.02,
) -> bool:
    """Whether a point lies on a segment, endpoints excluded."""
    if point in (start, end):
        return False
    (px, py), (x1, y1), (x2, y2) = point, start, end
    cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if length == 0.0 or abs(cross) > tolerance * length:
        return False
    dot = (px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)
    return 0.0 <= dot <= length**2


def load_schematic(info: SheetInfo) -> Schematic:
    return Schematic(info)
