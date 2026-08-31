"""DIP sockets; pin identities pass through to the installed IC."""

from enum import StrEnum
from .base import BoardComponent


Dip28Pin = StrEnum("Dip28Pin", {f"IC_PIN_{number}": str(number) for number in range(1, 29)})
Dip14Pin = StrEnum("Dip14Pin", {f"IC_PIN_{number}": str(number) for number in range(1, 15)})


class Dip28Socket(BoardComponent[Dip28Pin]):
    pin_type = Dip28Pin


class Dip14Socket(BoardComponent[Dip14Pin]):
    pin_type = Dip14Pin
