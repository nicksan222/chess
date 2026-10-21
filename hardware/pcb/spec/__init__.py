"""The PCB's specification: approved products, pins, wiring and board geometry.

Tool-independent inputs to the board build. Nothing here imports KiCad. The case
and plate take these facts from the board's published export.
"""

from .components import COMPONENTS, ComponentSpec

__all__ = ("COMPONENTS", "ComponentSpec")
