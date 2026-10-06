"""Complete package geometry: the pads of one exact component land pattern.

The data sits between a component's logical pin enum and the renderer's KiCad
footprint. Keeping it explicit makes package positions and physical pad
numbers reviewable instead of hiding them behind a library footprint name.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from .pad import Pad


@dataclass(frozen=True, slots=True)
class LandPattern[Pin: StrEnum]:
    """Map each logical pin to its numbered copper pads on a real package.

    A logical pin describes an electrical contact in the component API. A
    physical pad is the piece of copper that receives solder; several physical
    pads can share one logical pin when a package duplicates that contact.
    Coordinates are millimetres from the component centre and should come from
    the package drawing. ``pin_type`` is retained at runtime because Python's
    generic type parameter is not enough to validate enum members. This data
    replaces an opaque footprint name, but does not itself verify that the
    drawing was transcribed correctly.
    """

    pin_type: type[Pin]
    pads: tuple[Pad[Pin], ...]

    def __post_init__(self) -> None:
        """Require complete logical coverage and unique physical pad numbers.

        A missing logical pin would leave a component terminal without copper;
        a foreign pin would make the mapping ambiguous. Duplicate logical pins
        are intentional for packages with duplicated contacts, while duplicate
        physical numbers are rejected because KiCad needs one identity per pad.
        """
        if not isinstance(cast(object, self.pin_type), type) or not issubclass(
            self.pin_type, StrEnum
        ):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError("land pattern needs a pin enum type")
        if (
            not isinstance(cast(object, self.pads), (tuple, list))
            or not self.pads
            or any(
                not isinstance(cast(object, pad), Pad)
                or not isinstance(pad.pin, self.pin_type)
                for pad in self.pads
            )
        ):
            raise ValueError("land pattern pads must use its pin enum")
        object.__setattr__(self, "pads", tuple(self.pads))
        missing = set(self.pin_type) - {pad.pin for pad in self.pads}
        if missing:
            raise ValueError(
                f"land pattern missing pads for {sorted(map(str, missing))}"
            )
        numbers = [pad.physical_number for pad in self.pads]
        if len(set(numbers)) != len(numbers):
            raise ValueError("land pattern physical pad numbers must be unique")
