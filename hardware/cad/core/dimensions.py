"""CAD compatibility adapter for the shared physical dimensions.

Role: lets CAD generators write `from core import dimensions as shared` while the real
values live in `hardware/shared/dimensions/` (the contract with PCB and tests).
Nothing is defined here, so CAD cannot drift from the shared numbers. Running it as
a script validates the dimensions and prints a summary.

New hardware domains should import :mod:`shared.dimensions` directly.  CAD keeps
this module so existing generators can continue to use ``core.dimensions``.
"""

import sys
from pathlib import Path

# Blender runs generators with its own sys.path, so add `hardware/` explicitly to make
# the `shared` package importable.
HARDWARE_ROOT = Path(__file__).resolve().parents[2]
if str(HARDWARE_ROOT) not in sys.path:
    sys.path.insert(0, str(HARDWARE_ROOT))

# Re-export every shared dimension (the star import is the whole point of this module).
from shared.dimensions import *
from shared.dimensions import describe, validate

if __name__ == "__main__":
    validate()
    print(describe("CAD"))
