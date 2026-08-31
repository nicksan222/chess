"""IC sockets expose the semantic pins of the device installed in them."""

from .ahct125 import Ahct125Pin
from .base import BoardComponent
from .mcp23017 import Mcp23017Pin


class Dip28Socket(BoardComponent[Mcp23017Pin]):
    """Socket carrying one MCP23017 expander."""

    pin_type = Mcp23017Pin


class Dip14Socket(BoardComponent[Ahct125Pin]):
    """Socket carrying the SN74AHCT125 level shifter."""

    pin_type = Ahct125Pin
