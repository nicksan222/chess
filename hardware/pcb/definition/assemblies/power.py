"""Input protection, power distribution, and control-strip placement."""

from __future__ import annotations

import pcbnew

from pcb.definition.native import connect, place
from pcb.definition.parts import catalog as parts
from shared import dimensions
from shared import electronics as p
from shared.electronics import EndpointResolver


def add_strip[Part: EndpointResolver](
    board: pcbnew.BOARD,
    part: parts.PcbPart[Part],
    reference: str,
    *,
    assembly: str,
    purpose: str | None = None,
    nominal_value: str | None = None,
) -> Part:
    placement = dimensions.PCB_STRIP_PLACEMENTS[reference]
    return place(
        board,
        part,
        reference,
        at=placement.centre_mm,
        rotation=placement.rotation_degrees,
        assembly=assembly,
        purpose=purpose,
        nominal_value=nominal_value,
    )


def add_power(board: pcbnew.BOARD) -> None:
    jack = add_strip(
        board,
        parts.BARREL_JACK_PART,
        "J3",
        assembly="power",
    )
    fuse = add_strip(
        board,
        parts.FUSE_2A_PART,
        "F1",
        assembly="power",
    )
    switch = add_strip(
        board,
        parts.POWER_SWITCH_PART,
        "SW13",
        assembly="power",
    )
    tvs = add_strip(
        board,
        parts.TVS_6V8_PART,
        "D1",
        assembly="power",
    )
    bulk = add_strip(
        board,
        parts.CAP_1000U_PART,
        "C1",
        assembly="power",
        purpose="LED rail bulk capacitor",
    )
    bypass = add_strip(
        board,
        parts.CAP_10U_PART,
        "C2",
        assembly="power",
        purpose="Rail decoupling capacitor",
    )
    connect(
        board,
        "DC_IN",
        jack.pin(p.BarrelJackPin.CENTRE_POSITIVE),
        fuse.pin(p.FusePin.UNFUSED_INPUT),
    )
    connect(
        board,
        "DC_FUSED",
        fuse.pin(p.FusePin.FUSED_OUTPUT),
        switch.pin(p.PowerSwitchPin.FUSED_INPUT),
    )
    connect(
        board,
        "+5V",
        switch.pin(p.PowerSwitchPin.SWITCHED_FIVE_VOLTS),
        tvs.pin(p.TvsDiodePin.CATHODE_FIVE_VOLTS),
        bulk.pin(p.CapacitorPin.SUPPLY_OR_ELECTRODE_A),
        bypass.pin(p.CapacitorPin.SUPPLY_OR_ELECTRODE_A),
    )
    connect(
        board,
        "GND",
        jack.pin(p.BarrelJackPin.SLEEVE_GROUND),
        jack.pin(p.BarrelJackPin.SWITCHED_SLEEVE_GROUND),
        tvs.pin(p.TvsDiodePin.ANODE_GROUND),
        bulk.pin(p.CapacitorPin.RETURN_OR_ELECTRODE_B),
        bypass.pin(p.CapacitorPin.RETURN_OR_ELECTRODE_B),
    )
    for reference, net, description in (
        ("TP1", "+5V", "5 V test point"),
        ("TP2", "GND", "Ground test point"),
        ("TP5", "+3V3", "3.3 V test point"),
    ):
        probe = add_strip(
            board,
            parts.TEST_POINT_PART,
            reference,
            assembly="power",
            nominal_value=net,
            purpose=description,
        )
        connect(board, net, probe.pin(p.TestPointPin.PROBE))
