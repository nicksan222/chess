"""Reusable component definitions and complete placed component instances.

Define a product once in ``ComponentDefinition`` and reuse it for each placed
copy. ``BoardComponent`` supplies the instance-specific reference, placement,
purpose and complete pin map, then registers itself only after those facts
validate.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, cast

from .connections import Endpoint, NetConnection, NoConnect, PinConnection
from .geometry import Courtyard, Placement, Side
from .net import Net
from .pcbnew.escape import PackageRouting
from .pcbnew.land_pattern import LandPattern
from .pcbnew.point import Point
from .product import Product
from .spice.measurement import SpiceRequirement
from .spice.model import SpiceModel

if TYPE_CHECKING:
    from .registry import BoardRegistry


@dataclass(frozen=True, slots=True)
class ComponentDefinition[Pin: StrEnum]:
    """Facts shared by every copy of one exact component product.

    Construct this reusable kind before placing parts. It is not a footprint and
    it has no board reference or coordinates. ``product`` identifies the
    purchased part. ``pin_type`` names its allowed logical terminals using the
    numbers in its drawing. ``courtyard`` is the space a placed copy reserves.
    ``spice_model``, when present, selects a
    reusable electrical behavior and maps its ordered terminals to those pins.
    ``land_pattern``, when present, describes every numbered copper pad from
    the package drawing. No field contains a native footprint or raw SPICE
    program.
    """

    product: Product
    pin_type: type[Pin]
    courtyard: Courtyard
    spice_model: SpiceModel | None = None
    land_pattern: LandPattern[Pin] | None = None
    routing: PackageRouting = field(default_factory=PackageRouting)

    def __post_init__(self) -> None:
        """Reject empty pinouts and simulation terminals from another kind."""
        if not isinstance(cast(object, self.pin_type), type) or not issubclass(
            self.pin_type, StrEnum
        ):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError("component pins must be a StrEnum type")
        if not tuple(self.pin_type):
            raise ValueError("component definition needs at least one pin")
        if (
            self.product.body_mm[0] > self.courtyard.width_mm
            or self.product.body_mm[1] > self.courtyard.height_mm
        ):
            raise ValueError("product body must fit inside its courtyard")
        if any(
            not isinstance(path.pin, self.pin_type)
            for path in (*self.routing.paths, *self.routing.vias)
        ):
            raise ValueError("package paths must use component pins")
        if self.spice_model is not None and any(
            not isinstance(pin, self.pin_type) for pin in self.spice_model.terminals
        ):
            raise ValueError("SPICE model terminals must belong to this component")
        if self.land_pattern is not None and not isinstance(
            cast(object, self.land_pattern), LandPattern
        ):
            raise ValueError("land pattern must be a LandPattern")
        if (
            self.land_pattern is not None
            and self.land_pattern.pin_type is not self.pin_type
        ):
            raise ValueError("land pattern pins must belong to this component")
        if self.land_pattern is not None and any(
            abs(pad.center.x_mm) + pad.width_mm / 2 > self.courtyard.width_mm / 2
            or abs(pad.center.y_mm) + pad.height_mm / 2 > self.courtyard.height_mm / 2
            for pad in self.land_pattern.pads
        ):
            raise ValueError("land pattern copper must fit inside the courtyard")
        if self.land_pattern is not None and any(
            abs(pad.center.x_mm + point.x_mm) > self.courtyard.width_mm / 2
            or abs(pad.center.y_mm + point.y_mm) > self.courtyard.height_mm / 2
            for pad in self.land_pattern.pads
            for point in pad.polygon
        ):
            raise ValueError("custom pad copper must fit inside the courtyard")


@dataclass(frozen=True, slots=True)
class BoardComponent[Pin: StrEnum]:
    """One component instance with placement, every pin, and proof requests.

    This is the per-placement object created from a reusable
    ``ComponentDefinition``. Its reference, purpose, coordinates and pin map
    belong to this copy, not to the definition. The map must account for every
    declared pin once: either a board Net enum member, a detailed
    ``NetConnection``, or an explained no-connect. After all fields validate,
    construction automatically registers this instance in the board registry;
    failed construction therefore cannot leave a partial component behind.

    Bare net members become ``NetConnection`` objects internally, and the
    completed pin map is copied into a read-only view. A component kind can
    subclass this type to add electrical facts or standard proof requirements
    without exposing KiCad or SPICE syntax.
    """

    registry: BoardRegistry
    reference: str
    definition: ComponentDefinition[Pin]
    placement: Placement
    purpose: str
    pins: Mapping[Pin, PinConnection | Net]
    spice: tuple[SpiceRequirement, ...] = ()

    def __post_init__(self) -> None:
        """Validate the complete declaration before registering the instance."""
        if not self.reference.strip() or not self.purpose.strip():
            raise ValueError("placed component needs a reference and purpose")
        # StrEnum keys from different enum types compare equal when their text
        # matches. Identity of the pin *type* is therefore checked first.
        wrong_type = [
            pin for pin in self.pins if not isinstance(pin, self.definition.pin_type)
        ]
        if wrong_type:
            raise ValueError(
                f"{self.reference}: pins from another kind: {list(map(str, wrong_type))}"
            )
        expected = set(self.definition.pin_type)
        actual = set(self.pins)
        if missing := expected - actual:
            raise ValueError(
                f"{self.reference}: missing pins {sorted(map(str, missing))}"
            )
        if extra := actual - expected:
            raise ValueError(
                f"{self.reference}: unexpected pins {sorted(map(str, extra))}"
            )
        normalized: dict[Pin, PinConnection] = {}
        for pin, connection in self.pins.items():
            if isinstance(connection, Net):
                normalized[pin] = NetConnection(connection)
            elif isinstance(cast(object, connection), (NetConnection, NoConnect)):
                normalized[pin] = connection
            else:
                raise ValueError(f"{self.reference}: invalid pin connection")
        object.__setattr__(self, "pins", MappingProxyType(normalized))
        self.registry.register_component(self)

    def local_point(self, x_mm: float, y_mm: float) -> Point:
        """Transform package geometry through this instance's side and rotation."""
        placement = self.placement
        angle = math.radians(placement.rotation_degrees)
        if placement.side is Side.BOTTOM:
            x_mm = -x_mm
            angle = -angle
        cosine, sine = math.cos(angle), math.sin(angle)
        return Point(
            placement.x_mm + x_mm * cosine - y_mm * sine,
            placement.y_mm + x_mm * sine + y_mm * cosine,
        )

    def pin_position(self, pin: Pin) -> Point:
        """Position of a logical pin's primary physical pad in board coordinates."""
        self.endpoint(pin)
        pattern = self.definition.land_pattern
        if pattern is None:
            raise ValueError("pin position requires a land pattern")
        pads = sorted(
            (pad for pad in pattern.pads if pad.pin == pin),
            key=lambda pad: (pad.physical_number != str(pin), pad.physical_number),
        )
        point = pads[0].center
        if pattern.board_top_view and self.placement.side is Side.BOTTOM:
            angle = math.radians(self.placement.rotation_degrees)
            return Point(
                self.placement.x_mm
                + point.x_mm * math.cos(angle)
                - point.y_mm * math.sin(angle),
                self.placement.y_mm
                + point.x_mm * math.sin(angle)
                + point.y_mm * math.cos(angle),
            )
        return self.local_point(point.x_mm, point.y_mm)

    def port(self, name: str) -> Point:
        """A package-defined routing junction transformed with its placement."""
        try:
            point = dict(self.definition.routing.ports)[name]
        except KeyError as error:
            raise ValueError(f"unknown package port: {name}") from error
        return self.local_point(point.x_mm, point.y_mm)

    def endpoint(self, pin: Pin) -> Endpoint:
        """Select this instance's named physical contact as a routing anchor."""
        if not isinstance(pin, self.definition.pin_type):
            raise ValueError("pin must belong to this component")
        return Endpoint(self.reference, str(pin))

    def net(self, pin: Pin) -> Net:
        """Read the connected net from this instance's authoritative pin map."""
        self.endpoint(pin)
        connection = cast(PinConnection, self.pins[pin])
        if not isinstance(connection, NetConnection):
            raise ValueError(f"{self.reference}/{pin} is intentionally unconnected")
        return connection.net

    def pin_connections(self) -> tuple[tuple[Endpoint, PinConnection], ...]:
        """Return the one authoritative assignment of every numbered pin.

        Output follows the declared pin enum order, independently of the order
        used when the input dictionary was written. The registry uses this
        nongeneric view to combine unlike component kinds.
        """
        return tuple(
            (Endpoint(self.reference, str(pin)), cast(PinConnection, self.pins[pin]))
            for pin in self.definition.pin_type
        )

    def simulation_model(self) -> SpiceModel | None:
        """Return this component's declared electrical model, if one exists.

        A concrete kind may override this to include per-instance parameters,
        such as a resistor's ohmic value. Returning ``None`` means there is no
        model; circuit conversion must reject it rather than omit the part.
        """
        return self.definition.spice_model

    def product_parameters(self) -> tuple[object, ...]:
        """Return instance facts that must agree for one purchased part number.

        Concrete generic kinds override this for nominal electrical ratings.
        The registry compares these values across placements that name the
        same manufacturer and part number. Temporary operating state, such as
        whether a button is pressed in a static test, does not belong here.
        The shared definition itself is also compared by the registry.
        """
        return ()


class RegisteredComponent(Protocol):
    """The small common view the registry needs from unlike component kinds."""

    @property
    def reference(self) -> str:
        """Stable board designator of the component."""
        ...

    @property
    def spice(self) -> tuple[SpiceRequirement, ...]:
        """Electrical requirements owned by the component."""
        ...

    def pin_connections(self) -> tuple[tuple[Endpoint, PinConnection], ...]:
        """List the component's numbered pin assignments."""
        ...

    def simulation_model(self) -> SpiceModel | None:
        """Return the model that the circuit converter must render."""
        ...
