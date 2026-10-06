"""Per-layer line parameters and per-net bus capacitance from the routed board.

Line impedance and capacitance follow IPC-2141 microstrip, Z0 = 87 / sqrt(er + 1.41)
x ln(5.98 h / (0.8 w + t)), with C = sqrt(eeff) / (c Z0) and delay sqrt(eeff) / c.
Outer layers use the Hammerstad effective permittivity; buried layers are fully
embedded (eeff = er). h is the distance to the nearest plane layer (In1-In3) in the
PCBWay stackup (`datasheets.STACKUP_DIELECTRICS`), planes In1-In3 and In6; a layer with no
plane on one side
is treated as microstrip to the nearer plane, which is the low-capacitance bound for
the stripline-like inner layers and is offset by the +10 % stackup allowance.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

import pcbnew

from pcb.definition import rules
from spice import datasheets

LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu")
# In6 is the LED_5V plane since S6, so B.Cu and In5 are now plane-referenced too.
PLANES = frozenset({"In1.Cu", "In2.Cu", "In3.Cu", "In6.Cu"})
LIGHT_MM_PER_NS = 299.792458


@dataclass(frozen=True)
class Line:
    """Microstrip (outer) or embedded (inner) model of one routed layer: height to its nearest plane, permittivity,
    characteristic impedance and effective permittivity.
    """

    height_mm: float
    permittivity: float
    impedance: float
    effective_permittivity: float

    @property
    def farads_per_mm(self) -> float:
        # C = sqrt(eeff) / (c Z0), with c in mm/s.
        """Capacitance per millimetre, from C = sqrt(eeff) / (c x Z0)."""
        return math.sqrt(self.effective_permittivity) / (
            LIGHT_MM_PER_NS * 1e9 * self.impedance
        )

    @property
    def delay_ns_per_mm(self) -> float:
        """Propagation delay per millimetre, sqrt(eeff) / c."""
        return math.sqrt(self.effective_permittivity) / LIGHT_MM_PER_NS


def line(layer: str, width_mm: float = rules.TRACE_WIDTH_MM) -> Line:
    """The `Line` for a track of `width_mm` on `layer`, referenced to its nearest plane.

    Outer layers use the Hammerstad effective permittivity; inner layers are treated as
    embedded (eeff = er).
    """
    index = LAYERS.index(layer)
    best: tuple[float, float] | None = None
    for other, name in enumerate(LAYERS):
        if name not in PLANES or other == index:
            continue
        low, high = sorted((index, other))
        gaps = datasheets.STACKUP_DIELECTRICS[low:high]
        height = sum(t for t, _ in gaps) + datasheets.STACKUP_COPPER_MM * (
            high - low - 1
        )
        permittivity = max(dk for _, dk in gaps)
        if best is None or height < best[0]:
            best = (height, permittivity)
    assert best is not None
    height, er = best
    copper = datasheets.STACKUP_COPPER_MM
    impedance = (
        87 / math.sqrt(er + 1.41) * math.log(5.98 * height / (0.8 * width_mm + copper))
    )
    outer = layer in ("F.Cu", "B.Cu")
    effective = (
        (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 * height / width_mm)
        if outer
        else er
    )
    return Line(height, er, impedance, effective)


def via_farads(pad_mm: float = rules.VIA_PAD_MM) -> float:
    """Johnson & Graham 7.2 via-to-plane capacitance (inches in, picofarads out)."""
    thickness = 1.6 / 25.4
    pad = pad_mm / 25.4
    antipad = (pad_mm + 2 * rules.POUR_CLEARANCE_MM) / 25.4
    return 1.41 * datasheets.VIA_DK * thickness * pad / (antipad - pad) * 1e-12


@dataclass(frozen=True)
class NetCopper:
    """Routed copper of one net: track length per layer (mm) and the via count."""

    mm_by_layer: dict[str, float]
    vias: int

    @property
    def farads(self) -> float:
        """Estimated capacitance of the copper: tracks per layer plus the via-to-plane value,
        with the stackup tolerance allowance on the tracks.
        """
        tracks = sum(
            length * line(layer).farads_per_mm
            for layer, length in self.mm_by_layer.items()
        )
        return tracks * (1 + datasheets.STACKUP_TOLERANCE) + self.vias * via_farads()


def net_copper(board: pcbnew.BOARD, net: str) -> NetCopper:
    """Sum a net's routed track length per layer and count its vias, from the board."""
