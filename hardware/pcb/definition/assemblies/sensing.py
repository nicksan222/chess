"""Eight polled Hall banks, explicit P-port ownership and address straps."""

from __future__ import annotations

from collections.abc import Mapping

import pcbnew

from pcb.definition.assemblies.square import Square
from pcb.definition.bank_assemblies import BANK_ASSEMBLIES
from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts import catalog as parts
from shared import wiring
from shared.electronics import CapacitorPin, HallSensorPin, Tca9554Pin
from shared.electronics import Tca9554Component as Tca9554


def add_sensor_banks(
    board: pcbnew.BOARD,
    *,
    squares: Mapping[str, Square],
) -> None:
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
            assembly=bank_assembly.assembly_name,
            purpose="Expander decoupling capacitor",
            extras={"For": ref},
        )
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
        connect(board, wiring.SDA_NET, expander.pin(Tca9554Pin.I2C_DATA))
        connect(board, wiring.SCL_NET, expander.pin(Tca9554Pin.I2C_CLOCK))
        for pin, high in zip(
            (Tca9554Pin.ADDRESS_0, Tca9554Pin.ADDRESS_1, Tca9554Pin.ADDRESS_2),
            bank.straps,
            strict=True,
        ):
            connect(board, "+3V3" if high else "GND", expander.pin(pin))
        no_connect(board, expander.pin(Tca9554Pin.INTERRUPT))
        members = tuple(squares[position.name] for position in bank.members)
        for pin, member in zip(Tca9554.input_pins(), members, strict=True):
            connect(
                board,
                wiring.sense_net(member.name),
                expander.pin(pin),
                member.hall_sensor.pin(HallSensorPin.ACTIVE_LOW_OUTPUT),
            )
