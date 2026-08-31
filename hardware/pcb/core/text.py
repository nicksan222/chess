"""A minimal stroke font, so the board can label its own squares.

Silkscreen text needs outlines, and this toolchain has no font machinery. The
board only ever writes eight letters and eight digits, so a stroke font for those
is a few dozen line segments rather than a dependency.

Each glyph is a list of polylines on a unit box: x and y both run 0 to 1, so a
glyph scales to any height.
"""

from __future__ import annotations

Polyline = tuple[tuple[float, float], ...]

# Letters A-H and digits 1-8: everything a file or rank label needs.
GLYPHS: dict[str, tuple[Polyline, ...]] = {
    "A": (((0.0, 0.0), (0.5, 1.0), (1.0, 0.0)), ((0.22, 0.42), (0.78, 0.42))),
    "B": (
        ((0.0, 0.0), (0.0, 1.0), (0.7, 1.0), (0.9, 0.8), (0.7, 0.55), (0.0, 0.55)),
        ((0.7, 0.55), (0.95, 0.3), (0.7, 0.0), (0.0, 0.0)),
    ),
    "C": (((1.0, 0.85), (0.5, 1.0), (0.0, 0.7), (0.0, 0.3), (0.5, 0.0), (1.0, 0.15)),),
    "D": (((0.0, 0.0), (0.0, 1.0), (0.6, 1.0), (1.0, 0.6), (1.0, 0.4), (0.6, 0.0), (0.0, 0.0)),),
    "E": (
        ((1.0, 1.0), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0)),
        ((0.0, 0.5), (0.75, 0.5)),
    ),
    "F": (((1.0, 1.0), (0.0, 1.0), (0.0, 0.0)), ((0.0, 0.5), (0.75, 0.5))),
    "G": (
        ((1.0, 0.85), (0.5, 1.0), (0.0, 0.7), (0.0, 0.3), (0.5, 0.0), (1.0, 0.2)),
        ((1.0, 0.2), (1.0, 0.45), (0.55, 0.45)),
    ),
    "H": (((0.0, 1.0), (0.0, 0.0)), ((1.0, 1.0), (1.0, 0.0)), ((0.0, 0.5), (1.0, 0.5))),
    "1": (((0.25, 0.8), (0.55, 1.0), (0.55, 0.0)), ((0.2, 0.0), (0.9, 0.0))),
    "2": (((0.0, 0.85), (0.4, 1.0), (0.9, 0.8), (0.0, 0.0), (1.0, 0.0)),),
    "3": (
        ((0.0, 1.0), (0.85, 1.0), (0.4, 0.55)),
        ((0.4, 0.55), (0.95, 0.35), (0.7, 0.0), (0.05, 0.05)),
    ),
    "4": (((0.75, 0.0), (0.75, 1.0), (0.0, 0.3), (1.0, 0.3)),),
    "5": (((1.0, 1.0), (0.1, 1.0), (0.0, 0.55), (0.6, 0.6), (0.95, 0.35), (0.6, 0.0), (0.0, 0.1)),),
    "6": (((0.9, 0.9), (0.35, 1.0), (0.0, 0.4), (0.35, 0.0), (0.9, 0.2), (0.55, 0.5), (0.0, 0.4)),),
    "7": (((0.0, 1.0), (1.0, 1.0), (0.35, 0.0)),),
    "8": (
        ((0.5, 0.55), (0.1, 0.75), (0.5, 1.0), (0.9, 0.75), (0.5, 0.55)),
        ((0.5, 0.55), (0.05, 0.28), (0.5, 0.0), (0.95, 0.28), (0.5, 0.55)),
    ),
}

ASPECT = 0.62
SPACING = 0.28


def glyph_segments(
    character: str, x: float, y: float, height: float
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Line segments drawing one character, bottom-left anchored at (x, y)."""
    if character not in GLYPHS:
        raise KeyError(f"No glyph for {character!r}; the font covers {sorted(GLYPHS)}")
    width = height * ASPECT
    segments = []
    for polyline in GLYPHS[character]:
        points = [(x + px * width, y + py * height) for px, py in polyline]
        segments += list(zip(points, points[1:]))
    return segments


def text_width(label: str, height: float) -> float:
    width = height * ASPECT
    return len(label) * width + max(0, len(label) - 1) * height * SPACING


def text_segments(
    label: str, x: float, y: float, height: float, centre: bool = True
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Line segments drawing a label, optionally centred on (x, y)."""
    width = height * ASPECT
    advance = width + height * SPACING
    start_x = x - text_width(label, height) / 2.0 if centre else x
    start_y = y - height / 2.0 if centre else y
    segments = []
    for index, character in enumerate(label):
        segments += glyph_segments(character, start_x + index * advance, start_y, height)
    return segments
