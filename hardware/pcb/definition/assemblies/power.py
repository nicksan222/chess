"""Input protection, power distribution, and control-strip placement.

Role: the 'power' assembly: J4 (harness header), F1 (last-resort fuse), D1 (input TVS), the
U74 eFuse and its bias network, the bulk and bypass capacitors and the power test points,
and `add_strip`, the placement helper other assemblies share. The nets and the rocker-on-RUN
wiring follow the harness definition in `shared/electronics/harness.py`.
"""

from __future__ import annotations

import pcbnew

from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts import catalog as parts
from pcb.definition.parts.part import PcbPart
from shared import dimensions
from shared import electronics as p
from shared.electronics import EndpointResolver

# J4 F1 D1 U74 C1 C140 C2 C141 C142 C143 C144 R3-R8 TP1 TP2 TP5
ASSEMBLY_PART_COUNT = 20


def add_strip[Part: EndpointResolver](
    board: pcbnew.BOARD,
    part: PcbPart[Part],
    reference: str,
    *,
    assembly: str,
    purpose: str | None = None,
    nominal_value: str | None = None,
) -> Part:
    """Place a hand-placed part from the shared `PCB_STRIP_PLACEMENTS` table.

    Position, rotation and side all come from `shared/dimensions/panel.py`, so the PCB and the
    CAD clearance tests agree where the part is. `purpose`/`nominal_value` override the
    product defaults for the BOM and schematic.
    """
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
        bottom=placement.bottom,
    )


def add_power(board: pcbnew.BOARD) -> None:
    """J4 brings the harness in; fuse, TVS and the U74 eFuse follow it.

    Harness (interface H1, S4b): jack tip -> J4.1 DC_IN -> F1 -> DC_FUSED (U74 IN,
    D1, C141, R4) and J4.3 -> rocker -> J4.4 RUN; jack sleeve -> J4.2 GND. RUN
    (1k R8 wetting load) enables U74 through R6/R7 (604k/261k); OVLO from
    DC_FUSED through R4/R5 (604k/169k, 0.1 %) with C144 10 nF filtering hot-plug
    spikes (S4c); U74 OUT is the +5V rail.
    """
    header = add_strip(board, parts.POWER_HEADER_PART, "J4", assembly="power")
    fuse = add_strip(board, parts.FUSE_2A_PART, "F1", assembly="power")
    tvs = add_strip(board, parts.TVS_12V0_PART, "D1", assembly="power")
    efuse = add_strip(board, parts.EFUSE_PART, "U74", assembly="power")
    bulk = tuple(
        add_strip(
            board,
            parts.CAP_560U_PART,
            reference,
            assembly="power",
            purpose="LED rail bulk capacitor",
        )
        for reference in ("C1", "C140")
    )
    bypass = add_strip(
        board,
        parts.CAP_10U_PART,
        "C2",
        assembly="power",
        purpose="Rail decoupling capacitor",
    )
    efuse_input = add_strip(
        board, parts.CAP_1U_PART, "C141", assembly="power", purpose="eFuse input bypass"
    )

    def resistor(part: PcbPart[p.ResistorComponent], reference: str, purpose: str):
        return add_strip(board, part, reference, assembly="power", purpose=purpose)

    limit = resistor(parts.RES_1K65_PART, "R3", "eFuse current limit (ILM)")
    ovlo_top = resistor(parts.RES_604K_PRECISION_PART, "R4", "OVLO divider, top")
    ovlo_bottom = resistor(parts.RES_169K_PRECISION_PART, "R5", "OVLO divider, bottom")
    enable_top = resistor(
        parts.RES_604K_PRECISION_PART, "R6", "EN divider from RUN, top"
    )
    enable_bottom = resistor(parts.RES_261K_PART, "R7", "EN divider, bottom")
    wetting = resistor(parts.RES_1K_PART, "R8", "Rocker contact wetting load")
    ovlo_filter = add_strip(
        board, parts.CAP_10N_PART, "C144", assembly="power", purpose="OVLO spike filter"
    )
    slew = add_strip(
        board, parts.CAP_10N_PART, "C142", assembly="power", purpose="eFuse dVdt"
    )
    timer = add_strip(
        board, parts.CAP_1N_PART, "C143", assembly="power", purpose="eFuse ITIMER"
    )
    a, b = p.ResistorPin.TERMINAL_A, p.ResistorPin.TERMINAL_B
    supply, ground = (
        p.CapacitorPin.SUPPLY_OR_ELECTRODE_A,
        p.CapacitorPin.RETURN_OR_ELECTRODE_B,
    )
    connect(
        board,
        "DC_IN",
        header.pin(p.PowerHeaderPin.DC_INPUT),
        fuse.pin(p.FusePin.UNFUSED_INPUT),
    )
    connect(
        board,
        "DC_FUSED",
        fuse.pin(p.FusePin.FUSED_OUTPUT),
        header.pin(p.PowerHeaderPin.FUSED_TO_SWITCH),
        efuse.pin(p.EfusePin.INPUT),
        tvs.pin(p.TvsDiodePin.PROTECTED_INPUT),
        efuse_input.pin(supply),
        ovlo_top.pin(b),
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
