# Shared hardware definitions

This directory is the tool-independent contract between hardware domains.

- `dimensions.py` owns physical dimensions and placement coordinates.
- `components.py` owns component identity, package, and body metadata, plus the
  `ComponentImplementation` base class for tool-specific representations.

CAD, schematic, PCB, and future KiCad implementations may inherit from the base
class, but shared code must never import Blender, Schemdraw, Gerbonara, or KiCad.
Domain folders adapt these definitions and own only rendering/tool behavior.
