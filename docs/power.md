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
The suppressor and the fuse work as a pair. A spike is clamped; a reverse-polarity
or over-voltage supply makes the suppressor conduct hard enough to open the fuse
rather than letting the mistake reach the Pi. That pairing is why the board needs
no series protection diode, which at four amps would have to dissipate watts.

## Current budget

| Load | Draw |
|---|---|
| 64 SK9822 at unrestricted full white | about 3.84 A |
| Raspberry Pi Zero 2 W | about 0.4 A |
| Four expanders and the buffer | under 0.05 A |

That is roughly 4.3 A worst case against the approved 6 A supply. In normal use it sits well
under 1.5 A, because SK9822 carries a five-bit brightness field per LED and the
host caps it. Capping brightness is therefore part of the protocol rather than
something the application has to remember.

Pour generous 5 V and ground copper and place the bulk capacitor centrally in the
array, so the rail is injected across the entire playing area instead of being fed
through the chain. On a single board that costs nothing; the wiring harness of
revision A is what made power injection a problem worth documenting.

## Do not double-feed the Pi

Power the board from the barrel jack only. The Pi takes its 5 V through the
header, so also connecting its micro-USB port puts two supplies in opposition
across the same rail.

This is deliberately a documented constraint rather than a circuit. An ideal-diode
input selector would cost more complexity than the mistake is worth on a
prototype, and a plain series Schottky would drop the Pi's supply close to its
brown-out threshold.

## Watchdog

There is no separate processor to notice a hung host. Use the Pi's own SoC
watchdog through systemd's `RuntimeWatchdogSec`, which costs no extra parts.
