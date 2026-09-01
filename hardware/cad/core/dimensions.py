"""CAD compatibility adapter for the shared physical dimensions.

New hardware domains should import :mod:`shared.dimensions` directly.  CAD keeps
this module so existing generators can continue to use ``core.dimensions``.
"""

import sys
from pathlib import Path

HARDWARE_ROOT = Path(__file__).resolve().parents[2]
if str(HARDWARE_ROOT) not in sys.path:
    sys.path.insert(0, str(HARDWARE_ROOT))

from shared.dimensions import *
from shared.dimensions import describe, validate

if __name__ == "__main__":
    validate()
    print(describe("CAD"))
