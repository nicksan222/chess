"""Eight polled Hall banks, explicit P-port ownership and address straps.

Role: for each bank, places the TCA9554 I2C GPIO expander and its decoupling
capacitor, wires power/I2C/address straps, and connects each of the bank's eight
square sense nets to an expander input and that square's Hall sensor output.
Inputs: `BANK_ASSEMBLIES` (placement) and the `Square` handles from `square.py`.
"""

from __future__ import annotations

from collections.abc import Mapping

import pcbnew

from pcb.definition.assemblies.square import Square
from pcb.definition.bank_assemblies import BANK_ASSEMBLIES, TCA9554_BYPASS_ROTATION_DEG
from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts import catalog as parts
from shared import wiring
from shared.electronics import CapacitorPin, HallSensorPin, Tca9554Pin
from shared.electronics import Tca9554Component as Tca9554

# Footprints this assembly places per bank (expander + capacitor); the board
# validator multiplies it out to catch a missing or extra part.
ASSEMBLY_PART_COUNT = 2


def add_sensor_banks(
    board: pcbnew.BOARD,
    *,
    squares: Mapping[str, Square],
) -> None:
    """Place and wire every bank; `squares` maps "E4"-style names to handles."""
    for bank_assembly in BANK_ASSEMBLIES:
        bank = bank_assembly.bank
        ref = bank_assembly.expander_reference
        expander = place(
            board,
            parts.TCA9554_PART,
            ref,
            at=bank_assembly.expander_position_mm,
            assembly=bank_assembly.assembly_name,
            extras={"Bank": bank.label, "Address": f"0x{bank.address:02X}"},
        )
        bypass = place(
            board,
            parts.CAP_100N_PART,
            bank_assembly.bypass_reference,
            at=bank_assembly.bypass_position_mm,
            rotation=TCA9554_BYPASS_ROTATION_DEG,
            assembly=bank_assembly.assembly_name,
            purpose="Expander decoupling capacitor",
            extras={"For": ref},
        )
        # Decoupling cap shares the supply and ground nets with its expander.
        connect(
            board,
            "+3V3",
            expander.pin(Tca9554Pin.SUPPLY),
            bypass.pin(CapacitorPin.SUPPLY_OR_ELECTRODE_A),
        )
        connect(
            board,
            "GND",
            expander.pin(Tca9554Pin.GROUND),
            bypass.pin(CapacitorPin.RETURN_OR_ELECTRODE_B),
        )
        # I2C is a shared bus: every expander (and the display) joins the same nets.
        connect(board, wiring.SDA_NET, expander.pin(Tca9554Pin.I2C_DATA))
        connect(board, wiring.SCL_NET, expander.pin(Tca9554Pin.I2C_CLOCK))
        # Address pins are tied hard to +3V3 or GND from the bank index, giving each
        # expander a unique address (0x20 + index) with no jumpers.
        for pin, high in zip(
            (Tca9554Pin.ADDRESS_0, Tca9554Pin.ADDRESS_1, Tca9554Pin.ADDRESS_2),
            bank.straps,
            strict=True,
        ):
            connect(board, "+3V3" if high else "GND", expander.pin(pin))
        # Acquisition is polled, so the interrupt output is intentionally unused;
        # marking it no-connect keeps "every pin accounted for" validation true.
        no_connect(board, expander.pin(Tca9554Pin.INTERRUPT))
        # `members` order is the P0-P7 channel order; zip(strict) fails if the
        # bank ever has a different number of squares than expander inputs.
        members = tuple(squares[position.name] for position in bank.members)
        for pin, member in zip(Tca9554.input_pins(), members, strict=True):
            connect(
                board,
                wiring.sense_net(member.name),
                expander.pin(pin),
                member.hall_sensor.pin(HallSensorPin.ACTIVE_LOW_OUTPUT),
            )
