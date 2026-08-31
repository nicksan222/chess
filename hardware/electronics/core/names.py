"""Schematic compatibility adapter for the shared wiring contract."""

from pathlib import Path
import sys

HARDWARE_ROOT = Path(__file__).resolve().parents[2]
if str(HARDWARE_ROOT) not in sys.path:
    sys.path.insert(0, str(HARDWARE_ROOT))

from shared.wiring import *  # noqa: F403
