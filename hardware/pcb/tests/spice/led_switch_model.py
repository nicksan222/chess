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


def switch_rows(
    board: BoardHarness,
    *,
    lit: bool,
    rds_ohms: float,
    q1_vto: float = Q1_THRESHOLD_VOLTS,
    q2_vto: float = Q2_THRESHOLD_VOLTS,
) -> list[str]:
    """Q1/Q2 network and the chain; LED_EN is node `en_pi` (drive it externally).

    Nodes: `out` +5V, `led` LED_5V, `en_n` LED_EN_N, `q1g` Q1 gate.
    """
    _require_switch_topology(board)
    ohms = {ref: board.resistor_ohms(ref)[0] for ref in ("R13", "R14", "R15", "R16")}
    q1_kp = _kp(rds_ohms, Q1_GATE_DRIVE_VOLTS - abs(q1_vto))
    q2_kp = _kp(Q2_ON_OHMS, Q2_TEST_GATE_VOLTS - q2_vto)
    chain_amps = LED_COUNT * (
        datasheets.SK9822_STATIC_AMPS + 3 * datasheets.SK9822_CHANNEL_AMPS_MAX
    )
    if lit:
        load = (
            f"BCHAIN led 0 I={{{chain_amps} * 0.5 * (1 + tanh((V(led) - 3.0) / 0.1))}}"
        )
    else:
        load = f"RCHAIN led 0 {5.0 / (LED_COUNT * datasheets.SK9822_STATIC_AMPS)}"
    return [
        f".model Q1P PMOS(LEVEL=1 VTO={q1_vto} KP={q1_kp})",
        f".model Q2N NMOS(LEVEL=1 VTO={q2_vto} KP={q2_kp})",
        ".model Q1BODY D(IS=1e-12 N=1)",
        f"R13 en_pi en_g {ohms['R13']}",
        f"R14 en_g 0 {ohms['R14']}",
        "MQ2 en_n en_g 0 0 Q2N",
        f"R15 out en_n {ohms['R15']}",
        f"R16 en_n q1g {ohms['R16']}",
        "C145 q1g led 10n",
        # Si4403DDY: Ciss 3.25 nF, Crss 0.33 nF (VDS -10 V).
        "CQ1GS q1g out 2.92n",
        "CQ1GD q1g led 0.33n",
        "MQ1 led q1g out out Q1P",
        "DQ1 led out Q1BODY",
        f"CLED led 0 {LED_COUNT * 100e-9}",
        load,
    ]


def _schmitt(name: str, node: str, thresholds: tuple[float, float]) -> list[str]:
    """Schmitt input on `node` as a 0/1 state node `name` (VT-, VT+)."""
    low, high = thresholds
    return [
        (
            f"B{name}set {name}_s 0 V={{max(0.5*(1+tanh((V({node})-{high})/0.01)), "
            f"min(0.5*(1+tanh((V({node})-{low})/0.01)), V({name})))}}"
        ),
        f"R{name} {name}_s {name} 1k",
        f"C{name} {name} 0 10p",
    ]


# U75 input pins in the column order of SCES416N Table 1: In2, In1, In0.
U75_TABLE_PINS = (LogicGatePin.INPUT_2, LogicGatePin.INPUT_1, LogicGatePin.INPUT_0)
# Nets a U75 input may sit on: the two board signals, or a fixed level.
_GATE_SIGNAL = "LED_SW_GATE"
_FIXED_LEVELS = {"+5V": 1, "GND": 0}


def _u75_input_nets(board: BoardHarness) -> tuple[str, ...]:
    """The nets on U75's three inputs, refusing any wiring the behavioural model does not
    represent (so a layout change cannot make the model silently wrong).
    """
    nets = tuple(board.net_by_endpoint[("U75", str(pin))] for pin in U75_TABLE_PINS)
    allowed = {_GATE_SIGNAL, wiring.LED_ENABLE_N_NET, *_FIXED_LEVELS}
    if not set(nets) <= allowed:
        raise ValueError(f"U75 inputs on {nets}: not modelled")
    return nets
