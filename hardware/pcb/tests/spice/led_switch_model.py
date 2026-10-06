"""LED rail switch (S6, interface H5) as SPICE rows, built from the board's parts.

+5V (U74 OUT, node `out`) -> Q1 (Si4403DDY) -> LED_5V (node `led`). The Pi drives
LED_EN; R13 feeds Q2's gate, R14 holds it low; Q2 pulls LED_EN_N down against R15;
R16 and C145 (gate to drain) set Q1's turn-on ramp. Values come from the placed
parts. Q1 and Q2 are level-1 MOSFETs fitted to their datasheets [BEH]: Q1 VGS(th)
-0.4..-1 V (taken -0.7), RDS(on) 14 mOhm at VGS -4.5 V, Ciss 3.25 nF / Crss 0.33 nF
(Si4403DDY p2); Q2 VGS(th) 0.85-1.5 V (taken 1.2), 10 Ohm at 2.75 V (BSS138LT1/D).
The chain is 64 x 100 nF on LED_5V plus either its static current (blanked) or,
for an uninitialised chain that powers up lit, the full-white current once VDD
passes about 3 V (the LEDs' forward voltage; ASSUMPTION "LED power-up state").
"""

from __future__ import annotations

from shared import wiring
from shared.electronics.mosfet import (
    DRAIN_PINS,
    SOURCE_PINS,
    LogicGatePin,
    PowerMosfetPin,
    SmallMosfetPin,
)
from spice import datasheets
from spice.board_harness import BoardHarness

Q1_THRESHOLD_VOLTS = -0.7
Q1_THRESHOLD_CORNERS = (-0.4, -1.0)  # Si4403DDY p2 VGS(th) min/max.
Q2_THRESHOLD_CORNERS = (0.85, 1.5)  # BSS138LT1/D VGS(th) min/max.
Q1_GATE_DRIVE_VOLTS = 4.5
Q2_THRESHOLD_VOLTS = 1.2
Q2_TEST_GATE_VOLTS = 2.75
Q2_ON_OHMS = 10.0
LED_COUNT = 64


def _kp(ohms: float, overdrive: float) -> float:
    """Level-1 KP (W = L) giving `ohms` in the linear region at `overdrive`."""
    return 1 / (ohms * overdrive)


def _require_switch_topology(board: BoardHarness) -> None:
    """The rows below hard-code this topology: refuse a board that differs.

    Q1/Q2 pins by their datasheet roles (Si4403DDY 1-3 S, 4 G, 5-8 D; BSS138
    STYLE 21 1 G, 2 S, 3 D: `shared.electronics.mosfet`).
    """
    gate, rail = "LED_SW_GATE", wiring.LED_SUPPLY_NET
    enable, enable_n = wiring.LED_ENABLE_NET, wiring.LED_ENABLE_N_NET
    expected = {
        **{("Q1", str(pin)): "+5V" for pin in SOURCE_PINS},
        **{("Q1", str(pin)): rail for pin in DRAIN_PINS},
        ("Q1", str(PowerMosfetPin.GATE)): gate,
        ("Q2", str(SmallMosfetPin.GATE)): "LED_EN_GATE",
        ("Q2", str(SmallMosfetPin.SOURCE)): "GND",
        ("Q2", str(SmallMosfetPin.DRAIN)): enable_n,
    }
    pairs = {
        "R13": {enable, "LED_EN_GATE"},
        "R14": {"LED_EN_GATE", "GND"},
        "R15": {"+5V", enable_n},
        "R16": {enable_n, gate},
        "C145": {gate, rail},
    }
    nets = board.net_by_endpoint
    wrong = [key for key, net in expected.items() if nets.get(key) != net] + [
        (reference, "1-2")
        for reference, pair in pairs.items()
        if {nets.get((reference, "1")), nets.get((reference, "2"))} != pair
    ]
    if wrong:
        raise ValueError(f"LED switch differs from the modelled topology: {wrong}")
