"""Input protection, power distribution, and control-strip placement."""

from __future__ import annotations

import pcbnew

from pcb.definition.native import connect, place
from shared import dimensions
from shared import electronics as p
from shared.electronics import BarrelJackComponent as BarrelJack
from shared.electronics import CapacitorComponent as Capacitor
from shared.electronics import EndpointResolver
from shared.electronics import FuseComponent as Fuse
from shared.electronics import PowerSwitchComponent as PowerSwitch
from shared.electronics import TestPointComponent as TestPoint
from shared.electronics import TvsDiodeComponent as TvsDiode


def add_strip[Part: EndpointResolver](
    board: pcbnew.BOARD,
    model: Part,
    *,
    part_key: str,
    assembly: str,
    library: str,
    value: str,
    description: str,
) -> Part:
    x, y, rotation = dimensions.PCB_STRIP_PLACEMENTS_MM[model.reference]
    return place(
        board,
        model,
        part_key=part_key,
        at=(x, y),
        rotation=rotation,
        assembly=assembly,
        library=library,
        value=value,
        description=description,
    )


def add_power(board: pcbnew.BOARD) -> None:
    jack = add_strip(
        board,
        BarrelJack("J3"),
        part_key="BARREL_JACK",
        assembly="power",
        library="BARREL_JACK",
        value="DC 5.5x2.1",
        description="5 V DC input jack, centre positive",
    )
    fuse = add_strip(
        board,
        Fuse("F1"),
        part_key="FUSE_2A",
        assembly="power",
        library="FUSE",
        value="2 A time-delay",
        description="Input over-current protection matched to the 2.5 A jack",
    )
    switch = add_strip(
        board,
        PowerSwitch("SW13"),
        part_key="POWER_SWITCH",
        assembly="power",
        library="SWITCH",
        value="POWER",
        description="Latching power switch",
    )
    tvs = add_strip(
        board,
        TvsDiode("D1"),
        part_key="TVS_6V8",
        assembly="power",
        library="TVS",
        value="SMBJ6.0A",
        description="Input transient suppressor on the 5 V rail",
    )
    bulk = add_strip(
        board,
        Capacitor("C1"),
        part_key="CAP_1000U",
        assembly="power",
        library="C",
        value="1000uF 10V",
        description="LED rail bulk capacitor",
    )
    bypass = add_strip(
        board,
        Capacitor("C2"),
        part_key="CAP_10U",
        assembly="power",
        library="C",
        value="10uF 10V",
        description="Rail decoupling capacitor",
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
            TestPoint(reference),
            part_key="TEST_POINT",
            assembly="power",
            library="TESTPOINT",
            value=net,
            description=description,
        )
        connect(board, net, probe.pin(p.TestPointPin.PROBE))
