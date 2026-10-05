"""Typed native PCB part binding and registry validation."""

from collections.abc import Callable
from dataclasses import dataclass

import pcbnew

from shared.components import ComponentSpec
from shared.electronics import EndpointResolver


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
