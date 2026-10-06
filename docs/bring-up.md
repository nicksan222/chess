# Bring-up

## Purpose

This is the ordered first-article checklist for the D-PROTOTYPE board. Each step names
what to do, the pass threshold, and which `ASSUMPTIONS` entry it closes
(`hardware/pcb/definition/verification.py`, plus `CAD …` entries from
`hardware/shared/dimensions/unverified.py`). Electrical figures come from
[power](power.md) and are datasheet, calculated or simulated values, not measurements.

Rules:

- Stop at the first failure.
- Record the instrument, the value, the board serial and the date.
- Never write a value that was not measured.
- A threshold marked TBD has no owner value yet, and that step cannot pass.
- Only measured results, with provenance, go into `hardware/pcb/definition/evidence/`.

Probe points:

| Net | Where |
|---|---|
| `+5V` / `GND` | TP1 / TP2 |
| `+3V3` | TP5 |
| `LED_DATA_5V` / `LED_CLK_5V` | TP3 / TP4, or R17 / R18 pin 1 |
| `I2C_SCL` / `I2C_SDA` | TP6 / TP7 |
| `DC_FUSED` | D1 or C141 |
| `LED_5V` | Q1 pins 5-8 |
| `LED_SW_GATE` | Q1 pin 4 |
| `LED_EN_N` | Q2 pin 3, or U75 pin 1 |
| `LED_OE_N` | U5 pin 1, or U75 pin 4 |
| `RUN` | J4 circuit 4 |
| `LED_EN` | J1 socket pin 37, with GND at J1 pin 39 |

## Step 0: before ordering

These two steps gate the board order.

| # | Do | Pass | Closes |
|---|---|---|---|
| 0.1 | **Loose SK9822-A power-up.** Take 5-10 LEDs from the lot to be ordered, each with 100 nF, chained CKO→CKI and SDO→SDI. Feed them from a current-limited lab supply (0.1 A per LED). Ramp 0→5.0 V 20 times, and also switch 5.0 V on fast (about 1 ms, e.g. a MOSFET) 20 times. Hold the first LED's CKI and SDI through 10 kΩ to GND, as R17/R18 do on the board. An extra run with them floating is an optional stress case | No LED lights in any of the 40 starts (or 80 with the optional run); supply current < 5 mA per LED with no frame sent | `LED power-up state` (part; step 6.1 finishes it). **A fail blocks the order**: the board boot-loops with a lit chain |
| 0.2 | **Incoming PSU.** Measure the GST12A05-P1J output at no load and at 2.0 A (electronic load) | 4.75-5.25 V at both loads; **reject any unit above 5.25 V**. Ripple ≤ 80 mV p-p at 2.0 A (20 MHz bandwidth), as the models assume. Record the no-load margin to the OVLO low corner, **5.342 V** (the modelled peak, 5.25 V + 40 mV, leaves 52 mV) | `GST12A05 output` (part) |

## Step 1: fab and assembly records

| # | Do | Pass | Closes |
|---|---|---|---|
| 1.1 | Fab records: flying-probe e-test, stackup, hole-wall plating, CAM acceptance of the U74-only 0.16 mm / 0.20 mm rule | E-test pass. Stackup is 8-layer 1.6 mm, 1 oz. Plating is ≥ 18 µm. The fab accepted the scoped rule in writing | `Stackup`, `Via plating`, `U74 fine-pitch DRC` |
| 1.2 | Assembler records: SK9822-A dry-pack opening time and bake log, U74 MSL 2 handling | LED floor life ≤ 24 h before reflow, or baked per J-STD-033 | `LED moisture sensitivity` |
| 1.3 | **X-ray U74 first**, before any other inspection or power | No bridge across the 0.2 mm gaps, no open, all 10 terminals wetted (TI SLUA271 §5: x-ray shows bridges, opens, voids). Void area of each termination, including the IN/OUT/GND bars, **< 25 %** top-down: IPC's joint-area limit as summarised in Bernard, *Circuits Assembly*, 2019 (IPC-7093 itself not read). TI's ≤ 50 % applies to an exposed thermal pad, which the RPW package has none of | — (U74 assembly) |
| 1.4 | Visual/AOI checks | All 64 SK9822-A match the silk pin-1 dots (32 at 0°, 32 at 180°). Pin 1 is correct on U5, U74, U75 (placed at 180°: check against its silk dot), Q1, Q2, U1-U4 and U70-U73. C1/C140 polarity is correct. MLCC fillets are present. Bottom THT barrel fill is ≥ 75 % (IPC-A-610 class 2) | `MLCC lands`, `PTH copper rings`, `CAP_560U drill` (leads seated and filled) |

## Step 2: unpowered resistance (no Pi, harness unplugged)

| # | Do | Pass | Closes |
|---|---|---|---|
| 2.1 | F1, `DC_IN`→`DC_FUSED`, 4-wire | ≤ 0.1 Ω (0.0367 Ω nominal) | — |
| 2.2 | `RUN`→`GND` | 0.98-1.01 kΩ (R8 1 kΩ in parallel with R6+R7, 865 kΩ) [calc] | — |
| 2.3 | `DC_FUSED`→`GND` | > 100 kΩ (R4+R5 = 773 kΩ) [calc] | — |
| 2.4 | `+5V`, `LED_5V`, `+3V3`→`GND` | > 100 Ω after the capacitors charge, both meter polarities | — |
| 2.5 | `+5V`↔`LED_5V`, diode mode | Q1's body diode conducts only from `LED_5V` to `+5V`; no short | — |

## Step 3: harness and off-board parts

| # | Do | Pass | Closes |
|---|---|---|---|
| 3.1 | Continuity against [harness.md](../hardware/pcb/generated/harness.md) | J4.1→722A CENTER PIN; J4.2→722A **SLEEVE, not SLEEVE SHUNT**; J4.3/J4.4→rocker tabs | `Harness parts` |
| 3.2 | Rocker | J4.3-J4.4 open when off, < 0.1 Ω when on. It still works with the FASTONs swapped (a fit check; the RA1 drawing already shows two interchangeable 4.80 x 0.80 mm tabs, Off-On, contact 2-1) | — |
| 3.3 | Crimp pull test (VH and SH), one sacrificial crimp of each | Meets the JST crimp specification's pull force; read that value from the spec, not from here | `Harness parts` |
| 3.4 | OLED module, before fitting: SDA→VCC and SCL→VCC | ≥ 4.7 kΩ or open | `OLED pull-ups` (module) |
| 3.5 | J2 cavity 1 → module GND pad | Continuity | `J2 circuit 1` (wiring) |
| 3.6 | 722A contacts: 4-wire at 100 mA, centre and sleeve, from a Switchcraft S760 5.5 x 2.1 test plug's solder tail to the jack lug. Then the GST12A05 plug, 20 insertions, with a spring gauge | Each contact **≤ 0.01 Ω** (Switchcraft panel-mount DC jack spec: 0.01 Ω initial, 0.02 Ω after durability). GST plug insertion **≤ 13.3 N (3 lb)**, withdrawal **≥ 1.1 N (4 oz)** (same spec; applying it to the GST plug is our acceptance choice). The jack also states a 0.125 in (3.18 mm) maximum panel | `Jack/plug fit` |
| 3.7 | Mechanical, on the printed case | Rocker snaps into the panel and its cutout. 722A nut and washer (caliper) leave the 2.0 mm wall within thread. Both bays are deep enough. The mated VHR-4N clears the bottom keep volume. The SD card reaches its slot | `J4 back offset`; CAD `CASE_ROCKER_PANEL_THICKNESS_MM`, `CASE_ROCKER_CUTOUT_MM`, `CASE_ROCKER_BAY_DEPTH_MM`, `CASE_JACK_NUT_AND_WASHER_MM`, `CASE_JACK_BAY_DEPTH_MM`, `PI_SD_SOCKET_ON_PI_MM`, `PI_SD_SOCKET_HEIGHT_MM` |

## Step 4: first power (no Pi, `LED_EN` held low)

Use a lab supply at 5.00 V with a 0.1 A limit, fed through the harness and the 722A.
Fit three jumpers on the J1 socket:

- J1 pin 37 to pin 39 (`LED_EN` to GND);
- J1 pin 19 to pin 20 and pin 23 to pin 25. These ground U5's SPI inputs, which float without the Pi; a floating AHCT input can draw milliamps (SCLS264R ΔICC).

Keep the two SPI grounds through steps 4-6 and the `LED_EN` jumper through steps 4-5. **Remove all three before fitting the Pi**: the Pi drives pins 19, 23 and 37.

| # | Do | Pass | Closes |
|---|---|---|---|
| 4.1 | Rocker off | `+5V` < 0.1 V; supply current < 0.1 mA | — |
| 4.2 | Rocker on | `+5V` is 4.95-5.00 V and rises without overshoot. Idle input, read 2 min after rocker-on: **4.9-6.5 mA**. The budget is about 5.4 mA typical and ≤ 5.82 mA worst: R8 4.95-5.05 mA, U74 IQ ≤ 0.61 mA, C1/C140 leakage ≤ 0.11 mA, other ICs < 0.05 mA [DS/CALC]. Without the J1.19/J1.23 grounds the limit is ≤ 10 mA; record the reading either way | — |
| 4.3 | **LED rail off proof.** Check this with the jumper fitted and again with J1.37 open (R14 alone) | `LED_EN_N` = `+5V` ±50 mV; `LED_SW_GATE` = `+5V` ±50 mV; **`LED_5V` < 0.1 V**; **`LED_OE_N` = `+5V` ±50 mV** (U5 disabled); **TP3/TP4 ≤ 0.1 V** (held by R17/R18; 25 mV at U5's maximum off-state leakage, IOZ 2.5 µA x 10 kΩ) | — (required before step 5) |
