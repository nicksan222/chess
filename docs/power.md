# Power

## Purpose

Describe how the board is powered and where the current goes.

## No conversion on the board

A MEAN WELL GST12A05-P1J 5 V 2 A regulated supply feeds a Switchcraft 722A panel
jack in the case's rear wall, and that is the rail. There is no buck converter, no
inductor, no USB power negotiation and no battery. The 3.3 V the expanders and the
display need comes off the Raspberry Pi's own header.

The power path is a harness plus an on-board eFuse. Four wires join the panel jack
and the panel rocker (E-Switch RA11131100, also in the rear wall) to J4, a JST
B4PS-VH header on the board's bottom side (generated
[harness table](../hardware/pcb/generated/harness.md)):

| J4 circuit | Net | Goes to |
|---|---|---|
| 1 | `DC_IN` | jack centre pin, then F1 on the board |
| 2 | `GND` | jack sleeve |
| 3 | `DC_FUSED` | rocker, after F1 |
| 4 | `RUN` | rocker, other tab: the eFuse enable signal |

On the board: `DC_IN` goes through F1 (Littelfuse 0453002.MR, 2 A very fast-acting
surface-mount fuse, kept as the last-resort fuse) to `DC_FUSED`, which feeds the
TI TPS259474ARPWR eFuse (U74); its output is the `+5V` plane. D1, an SMBJ12CA
bidirectional TVS, sits on `DC_FUSED`. **The rocker no longer carries load current**:
it connects `DC_FUSED` to `RUN`, which enables the eFuse through a divider, and a
1 kΩ load (R8, about 5 mA) keeps the contacts wetted. Bulk storage is two Rubycon
560 µF electrolytics (C1, C140) on the bottom side plus a 10 µF ceramic (C2) next to
J4; each IC and LED has its own 100 nF capacitor.

The 64 LEDs do not hang directly on `+5V`: they run from a separate `LED_5V` plane
(inner layer 6), switched from `+5V` by a P-channel MOSFET (Q1, Vishay Si4403DDY),
so the LED rail can be off while the Pi boots. See "LED rail switch" below.

## Protection

Figures are from SPICE of the routed board at worst-case corners with a behavioural
eFuse built from datasheet tables (no vendor model), plus datasheet values; they are
not measurements.

- **Inrush and current limit:** the eFuse's dVdt capacitor sets a slow start; a
  hot-plug uses 0.0034 A²s, 0.64 % of the fuse's 0.530 A²s melting I²t (the usual rule
  is under 20 %). Above 1.80-2.20 A (ILIM) the eFuse's circuit breaker opens after its 0.46-1.6 ms
  fault timer (C143, 1 nF) and auto-retries 110 ms later; above about twice ILIM it trips
  at once and then limits at ILIM; during start-up it limits at ILIM (datasheet SLVSFC9C
  7.3.5, simulated with a behavioural model).
- **Over-voltage lockout (OVLO):** the output is cut above 5.342-5.663 V (restart
  4.854-5.173 V), set by a 604 kΩ/169 kΩ divider with a 10 nF filter (C144) so that
  a hot-plug ring on the cord does not lock the board out. TI requires divider
  resistors of at least 350 kΩ on input-referred pins for the reverse-polarity
  protection to hold. A 12 V adapter trips in about 1.04 ms with the rail at 0.36 V; 6 V,
  7 V and 12 V wrong adapters are refused safely at every corner (rail 0, the TVS stays
  off). The cut-off **latches**: after any over-voltage event, unplug and replug the
  supply; returning to 5.25 V does not restart it, and 5.0 V restarts only at one
  corner.
- **Surge clamp:** at the SMBJ12CA's clamp voltage the eFuse enable pin keeps 0.5 V of
  margin to its limit.
- **Reverse polarity:** the eFuse input is rated to -15 V; a reversed 5.25 V plug leaves
  the rail at 0 V, and the TVS does not conduct. **Avoid reversed 12 V adapters**: the
  model puts about 20 µA into the eFuse's enable and over-voltage pins, above TI's 10 µA
  limit for the reverse-polarity protection (an assumption with a test bound, not a
  closed risk).
- **Residual risks (assumptions, not closed):**
  - The window's top corner (5.663 V) is above the SK9822-A's 5.5 V absolute maximum
    and its 5.3 V recommended maximum, so a supply failing into 5.5-5.66 V stays on.
    A 5.25 V supply (the GST12A05's +5 % limit) is inside 5.3 V.
  - A supply that steps up to 6-7 V while running trips after about 0.7-1.7 ms, but
    the bulk capacitors hold the rail above 5.5 V for about 10 ms, with a peak of about
    6 V on the LEDs. D1 (SMBJ12CA, breakdown 13.3-14.7 V) does not clamp at 6-7 V.
- **Acceptance criterion:** the rail must stay at or above 4.5 V (the SK9822 and
  AHCT125 minimum) at the worst corner: supply at -5 % (4.75 V), end-of-life contact
  resistance, fuse resistance at 1.5 x cold, 70 °C copper, Q1 at its hot maximum
  resistance, the approved LED load at 18 mA per channel. The model gives 4.518 V at
  the LEDs and 4.525 V at the Pi header (Q1 drops 6.5 mV). The Pi's 4.63 V
  under-voltage level is **not met** at the worst corner; the
  Zero has no detector, so this is a bench check (`vcgencmd get_throttled` at the
  low corner), not a design pass.
- **Full white:** an unrestricted full-white frame draws 3.97 A including the host.
  Depending on the part's ILIM, the eFuse either trips at once and limits at 1.8-2.2 A
  (rail about 3 V) or passes the full load until its breaker opens within 1.6 ms; either
  way the Pi browns out and the fuse sees at most 0.025 A²s (4.7 % of its melting I²t).
  The approved load is below the 1.80 A minimum trip point.
- **Not modelled:** the eFuse vendor model and its thermal shutdown. Start-up limiting,
  the breaker, the fast trip and the auto-retry are simulated from the datasheet; how long
  it limits before thermal shutdown is a bench item.

## Current budget

| Load | Draw |
|---|---|
| 64 SK9822-A at unrestricted full white (budgeted at 18 mA per channel) | 3.97 A including the host (above the 2 A supply and fuse) |
| Raspberry Pi Zero 2 W | about 0.4 A (included above) |
| Eight expanders and the buffer | small; not separately budgeted |

Full white is therefore not allowed. `hardware/pcb/definition/manufacturing.json`
sets the approved LED limit at a global brightness of 3/31 (the SK9822-A has a
five-bit brightness field per LED), and `tests/board/test_power_budget.py` checks that
limit against the 2 A supply and fuse ratings. Capping brightness is part of the
protocol, not something the application has to remember.

Copper is sized for the 2 A fuse rating: input traces are 1.5 mm and each plane entry
is checked at 2 A (IPC-2221 steady state, 10 °C rise, `tests/board/test_ampacity.py`).
A resistor-mesh SPICE model of the +5V and ground planes puts the worst-LED drop at
1.44 mV at the approved limit and 7.9 mV at full white against a 50 mV budget
(`tests/spice/plane_mesh.py`). These are calculations and simulations, not
measurements.

The protection analysis above covers supply-to-Pi voltage, inrush against the fuse's
I²t and the fault cases. Until the bench items below are done, the power path is not
qualified.

## LED rail switch

The LEDs are **off at boot**. A 100 kΩ pull-down holds `LED_EN` (BCM 26, header
pin 37) low, which keeps Q1 off. The 74AHCT125 buffer's outputs are high-impedance
until the LED rail is up: a TI SN74LVC1G97 (U75) combines the switch's gate and enable
signals into the buffer's output enables, so the buffer cannot drive the LED inputs
early, and it disables the outputs within about 1 µs when the rail switches off. While the buffer
is off, 10 kΩ pull-downs (R17/R18) hold the first LED's data and clock inputs low. Without
the switch a chain left in a lit state would draw about 4 A at power-up, which trips the
eFuse (immediately into 1.8-2.2 A limiting, or by the breaker within 1.6 ms). The firmware contract (`hardware/shared/electronics/sk9822.py`):

1. Set `LED_EN` high.
2. Stream **blank frames for at least 10 ms** (the blanking period). The buffer passes
   them to the LEDs about 2-3 ms after `LED_EN` rises (simulated 1.78-3.05 ms, with the
   LED rail at 4.6 V or more by then); frames sent earlier are dropped. Then send
   normal frames.
3. To switch off, send a blank frame, then take `LED_EN` low.

SPI clock at most 10 MHz. Frame: 32 zero bits, per LED `111` + 5-bit brightness then
Green, Red, Blue bytes (the SK9822-A order), then an end frame of `max(32, ceil(N/2))`
one bits for N LEDs. The simulation gives the LED rail a 10-90 % rise of about 0.95 ms
with a blanked chain, and a 0.56 A input peak. **A chain that powers up lit is not safe**:
in simulation `+5V` falls below the Pi's 4.63 V within about 3 ms, whichever way the
eFuse trips, which makes the board boot-loop. That residual is recorded as an assumption; bench it by enabling an
uninitialised chain. With the buffer held off, the LED data and clock inputs stay within
0.12 V of the LED rail in simulation (including the buffer's maximum off-state leakage;
limit 0.3 V above it) and within 25 mV of ground while the buffer is off.

## Never power the Pi from its own USB while it is fitted

This is deliberately a documented constraint rather than a circuit. An ideal-diode
input selector would cost more complexity than the mistake is worth on a
prototype, and a plain series Schottky would drop the Pi's supply close to its
brown-out threshold.

## Watchdog

There is no separate processor to notice a hung host. Use the Pi's own SoC
watchdog through systemd's `RuntimeWatchdogSec`, which costs no extra parts.
