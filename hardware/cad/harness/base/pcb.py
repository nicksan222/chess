"""Read PCB-owned assembly metadata without rebuilding electronics in CAD."""

from pcb.board.assembly import PcbPart, PcbSnapshot
from pcb.board.interface import HarnessRun

__all__ = ("HarnessRun", "PcbPart", "PcbSnapshot")
