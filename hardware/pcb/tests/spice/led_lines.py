"""LED clock/data links as lossless transmission lines built from the routed copper.

Every routed segment of a link's nets becomes a lossless line with the layer's
IPC-2141 impedance and delay (`bus_lines.line`), split where another segment or a
via joins it; vias add their plane capacitance; pads join the segment ends they
contain. A series resistor between two nets (R9 on the first data link) joins its
pads. The driver is a ramp behind a resistance, the receiver an SK9822 input
(`datasheets.SK9822_INPUT_FARADS`, verification ASSUMPTION "SK9822 input").

Each edge records the receiver's peak/trough (`result_<tag>_peak` / `_trough`) and
`_hold`: after the receiver first crosses the far threshold (0.7 / 0.3 x VDD) it must
stay past it, so the edge is monotonic through the threshold band and clocks once.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import pairwise

import pcbnew

from shared.electronics import Ahct125Pin, Sk9822Pin
from spice import datasheets
from spice.board_harness import BoardHarness
from spice.bus_lines import Line, line, via_farads
from spice.circuit import SpiceCircuit
