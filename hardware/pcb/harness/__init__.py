"""The beginner-facing API for declaring one typed board design.

Start with a ``Net`` subclass for the board's electrical vocabulary, then use
``Circuit.place`` with reusable ``ComponentDefinition`` objects and physical
``Placement``/``Courtyard`` facts. A placed component registers itself after its
complete pin map validates. ``Circuit.check`` adds named simulation scenarios;
``Circuit.write_board`` is the separate boundary that requires PCB outline and
land-pattern facts before handing the declaration to KiCad. Lower-level types
remain public for custom component kinds and converter tests, but board authors
normally do not need to assemble raw SPICE syntax.
"""

from .base.circuit import Circuit
from .base.component import BoardComponent, ComponentDefinition
from .base.connections import Endpoint, NetConnection, NoConnect
from .base.geometry import Courtyard, Placement, Side
from .base.net import Net
from .base.pcbnew import (
    BoardOutline,
    CopperLayer,
    LandPattern,
    Pad,
    PadKind,
    PadShape,
    Point,
    Trace,
    Via,
)
from .base.pcbnew.escape import EscapeAxis, PackageRouting
from .base.pcbnew.package_copper import PackageClearance, PackagePath, PackageVia
from .base.pcbnew.routing.definition import (
    Bend,
    CopperPath,
    DirectLink,
    NetRoute,
    PinLaunch,
    RouteStage,
    RoutingPlan,
)
from .base.product import Product
from .base.registry import BoardRegistry
from .base.spice import (
    AcSweep,
    CurrentSource,
    CurrentThrough,
    DcVoltage,
    Limit,
    ModelParameter,
    Observation,
    OperatingPoint,
    PulseVoltage,
    SpiceModel,
    SpiceRequirement,
    SpiceScenario,
    Transient,
    VoltageAt,
    VoltageBetween,
    VoltageSource,
)
from .base.spice.render import render_deck, run_deck, write_deck
from .base.spice.state import StateChange

__all__ = (
    "AcSweep",
    "Bend",
    "BoardComponent",
    "BoardOutline",
    "BoardRegistry",
    "Circuit",
    "ComponentDefinition",
    "CopperLayer",
    "CopperPath",
    "Courtyard",
    "CurrentSource",
    "CurrentThrough",
    "DcVoltage",
    "DirectLink",
    "Endpoint",
    "EscapeAxis",
    "LandPattern",
    "Limit",
    "ModelParameter",
    "Net",
    "NetConnection",
    "NetRoute",
    "NoConnect",
    "Observation",
    "OperatingPoint",
    "PackageClearance",
    "PackagePath",
    "PackageRouting",
    "PackageVia",
    "Pad",
    "PadKind",
    "PadShape",
    "PinLaunch",
    "Placement",
    "Point",
    "Product",
    "PulseVoltage",
    "RouteStage",
    "RoutingPlan",
    "Side",
    "SpiceModel",
    "SpiceRequirement",
    "SpiceScenario",
    "StateChange",
    "Trace",
    "Transient",
    "Via",
    "VoltageAt",
    "VoltageBetween",
    "VoltageSource",
    "render_deck",
    "run_deck",
    "write_deck",
)
