"""Reusable electrical component kinds independent of any particular board.

Each class adds its electrical facts to ``BoardComponent``. A board author
still provides the exact product, land pattern, placement and connections when
placing one instance with ``Circuit.place``. These generic kinds deliberately
contain no board-specific part number or location.
"""

from .button import Button, ButtonPin, ButtonState
from .capacitor import Capacitor, CapacitorPin
from .diode import Diode, DiodePin
from .resistor import Resistor, ResistorPin

__all__ = (
    "Button",
    "ButtonPin",
    "ButtonState",
    "Capacitor",
    "CapacitorPin",
    "Diode",
    "DiodePin",
    "Resistor",
    "ResistorPin",
)
