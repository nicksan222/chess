"""Typed native PCB part binding and registry validation.

Role: `PcbPart` ties one approved product (`ComponentSpec`) to its typed pin model and
its native footprint template, plus the display defaults shown in the BOM and
schematic. `parts/catalog.py` lists every binding and `native.place()` consumes them.
Validating at construction (import) time means an inconsistent binding fails
immediately rather than producing a quietly wrong board.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import pcbnew

from shared.components import ComponentSpec
from shared.electronics import EndpointResolver


class DrawingView(Enum):
    """Which side the template's land drawing is seen from.

    MOUNTING_SIDE: the datasheet layout as seen from the side the part sits on
    (KiCad and most catalogues, e.g. JST VH p4 note 1). On the bottom it needs a
    true mirror flip. BOARD_TOP: holes defined by a mating part seen from the
    board top (the Pi header), so a bottom placement keeps them unmirrored.
    """

    MOUNTING_SIDE = "mounting side"
    BOARD_TOP = "board top"


@dataclass(frozen=True)
class PcbPart[Part: EndpointResolver]:
    """One approved product's logical model, land pattern, and display defaults."""

    spec: ComponentSpec
    model: Callable[[str], Part]
    template: pcbnew.FOOTPRINT
    library: str
    nominal_value: str
    default_purpose: str

    def __post_init__(self) -> None:
        if not all((self.library, self.nominal_value, self.default_purpose)):
            raise ValueError(f"{self.spec.key}: PCB display defaults must not be empty")
        if self.template.GetFieldText("Package") != self.spec.package:
            raise ValueError(
                f"{self.spec.key}: footprint package does not match product"
            )
        if not self.model("REGISTRY_CHECK").supports_part_key(self.spec.key):
            raise ValueError(
                f"{self.spec.key}: electronic model does not support product"
            )

    def new_model(self, reference: str) -> Part:
        """Construct the typed logical model selected by this registry entry."""
        return self.model(reference)
