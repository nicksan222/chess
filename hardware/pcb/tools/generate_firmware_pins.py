#!/usr/bin/env python3
"""Generate type-safe firmware pins from the native KiCad board."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = PCB_ROOT.parent
REPOSITORY_ROOT = HARDWARE_ROOT.parent
for path in (PCB_ROOT, HARDWARE_ROOT):
    sys.path.insert(0, str(path))

from board import artifacts
from kicad.api import pcbnew

BOARD_PATH = artifacts.BOARD
OUTPUT_PATH = REPOSITORY_ROOT / "apps/firmware/src/generated_pins.rs"
HOST_HEADER_REFERENCE = "J1"

# Raspberry Pi 40-pin header identity. This is a property of the host, not this
# board's interpretation of a line. pcbnew remains authoritative for which of
# these pins the PCB actually connects.
_BCM_BY_HEADER_PIN = {
    3: 2,
    5: 3,
    7: 4,
    8: 14,
    10: 15,
    11: 17,
    12: 18,
    13: 27,
    15: 22,
    16: 23,
    18: 24,
    19: 10,
    21: 9,
    22: 25,
    23: 11,
    24: 8,
    26: 7,
    27: 0,
    28: 1,
    29: 5,
    31: 6,
    32: 12,
    33: 13,
    35: 19,
    36: 16,
    37: 26,
    38: 20,
    40: 21,
}
_IGNORED_NETS = frozenset({"+3V3", "+5V", "GND"})


@dataclass(frozen=True, order=True)
class ConnectedPin:
    """One signal GPIO observed on the native host-header footprint."""

    bcm: int
    header_pin: int
    net: str


def connected_pins(board_path: Path = BOARD_PATH) -> tuple[ConnectedPin, ...]:
    """Read connected host GPIOs from pcbnew's native board model."""
    board = pcbnew.LoadBoard(str(board_path))
    header = board.FindFootprintByReference(HOST_HEADER_REFERENCE)
    if header is None:
        raise ValueError(f"{board_path}: no {HOST_HEADER_REFERENCE} host header")

    pads = tuple(header.Pads())
    if len(pads) != 40:
        raise ValueError(
            f"{HOST_HEADER_REFERENCE}: expected a 40-pin Raspberry Pi header, "
            f"found {len(pads)} pads"
        )

    found: list[ConnectedPin] = []
    for pad in pads:
        header_pin = int(pad.GetNumber())
        net = pad.GetNetname()
        if not net or net in _IGNORED_NETS or net.startswith("unconnected-("):
            continue
        try:
            bcm = _BCM_BY_HEADER_PIN[header_pin]
        except KeyError as error:
            raise ValueError(
                f"{HOST_HEADER_REFERENCE} pin {header_pin} carries signal net "
                f"{net!r}, but is not a Raspberry Pi GPIO"
            ) from error
        found.append(ConnectedPin(bcm, header_pin, net))

    pins = tuple(sorted(found))
    if len({pin.bcm for pin in pins}) != len(pins):
        raise ValueError("native board connects one BCM GPIO more than once")
    return pins


def render(board_path: Path = BOARD_PATH) -> str:
    """Render the board's connected GPIO identities as readable Rust."""
    definitions = []
    for pin in connected_pins(board_path):
        definitions.append(
            f"""/// BCM GPIO {pin.bcm}, on physical header pin {pin.header_pin}.
///
/// The current PCB net is `{pin.net}`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio{pin.bcm};

impl RaspberryPiPin for Gpio{pin.bcm} {{
    const BCM_NUMBER: u8 = {pin.bcm};
    const HEADER_PIN: u8 = {pin.header_pin};
}}"""
        )

    definition_block = "\n\n".join(definitions)
    if definitions:
        definition_block += "\n"
    return f"""// @generated from pcbnew's native board model; do not edit.

/// A Raspberry Pi GPIO that the native PCB connects.
///
/// This trait describes only host pin identity. Consumers provide the concrete
/// GPIO implementation and assign application meaning to each marker type.
pub trait RaspberryPiPin {{
    /// Broadcom GPIO line number used by Linux GPIO interfaces.
    const BCM_NUMBER: u8;

    /// Physical position on the Raspberry Pi 40-pin header.
    const HEADER_PIN: u8;
}}

{definition_block}"""


def main() -> None:
    """Write generated Rust or reject stale checked-in output."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when generated firmware pins are stale",
    )
    arguments = parser.parse_args()
    expected = render()
    current = OUTPUT_PATH.read_text() if OUTPUT_PATH.exists() else None
    if arguments.check:
        if current != expected:
            raise SystemExit(
                "firmware pins are stale; run `just --justfile hardware/pcb/justfile pins`"
            )
        return
    OUTPUT_PATH.write_text(expected)


if __name__ == "__main__":
    main()
