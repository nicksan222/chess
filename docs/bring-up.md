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

Run every over-voltage and current-limit test below only after 4.3 passes. Keep the
`LED_EN` jumper to GND fitted through step 5, so the LEDs sit behind an open Q1. **Do not
fit the Pi for steps 4-6.**

## Step 5: eFuse (no Pi, lab supply ≥ 3 A, scope on `DC_FUSED`, `+5V`, `LED_5V`)

| # | Do | Pass | Closes |
|---|---|---|---|
| 5.1 | **OVLO trip.** Ramp 5.00→5.70 V in 10 mV steps of about 1 s each. Never exceed 5.70 V | `+5V` goes to 0 at **5.342-5.663 V**; `LED_5V` stays < 0.1 V | `OVLO window` (trip) |
| 5.2 | **OVLO latch.** After the trip, ramp down to 5.25 V, then on down to 4.80 V. Then turn the supply off and on at 5.00 V | Stays off at 5.25 V. Any restart on the way down falls within **4.854-5.173 V** (record it). Power-cycling at 5.00 V restarts the rail | `OVLO window` (restart and latch; the user manual must say "unplug and replug") |
| 5.3 | **Running step.** Load `+5V` with 78 Ω (≥ 1 W) or a 64 mA CC e-load at TP1/TP2, matching the model's 64-LED static load. Rail on at 5.00 V, then step to 6.0 V in **≤ 50 µs** (a MOSFET between two supplies, or a programmable supply with that slew). Record the `DC_FUSED` edge | Trip delay (`DC_FUSED` crossing 5.9 V to `+5V` falling) **≤ 2.0 ms**; `+5V` above 5.5 V for **≤ 12 ms**; `LED_5V` < 0.1 V. Results of 2.0-3.5 ms or 12-21 ms are recorded and sent to hardware as a model discrepancy, not an automatic reject | `OVLO filter` |
| 5.4 | Cold-plug 6.0 V and 7.0 V | `+5V` stays 0 V; D1 cold | `OVLO window` (wrong adapter) |
| 5.5 | **Circuit breaker, one trip.** Supply 5.00 V / ≥ 3 A. Step a CC e-load on `+5V` (C1/C140 leads) 0→**2.5 A**, then off after the first retry. 2.5 A exceeds ILIM (1.80-2.20 A) at every corner and stays below the 3.6 A fast trip. Its I²t per trip is ≤ 0.010 A²s, 1.9 % of F1's 0.530 A²s (ITIMER C143 1 nF). Optional, to find ILIM: a CC staircase from 1.70 to 2.30 A in 50 mA steps, each held ≥ 5 ms | `+5V` stays up while the load draws the full 2.5 A (the TPS259474A passes the full load until the timer expires; it does not limit at ILIM). It turns off **0.46-1.6 ms** after the step; auto-retry after about **110 ms** (tRST). Staircase: the first step that trips is within **1.80-2.20 A** | `eFuse model` (breaker) |
| 5.6 | **Hot plug.** Plug the real GST12A05 in 20 times, then switch on with the rocker 20 times | `+5V` comes up 40/40 with no OVLO latch; `+5V` peak ≤ 5.5 V; `DC_FUSED` ring and inrush recorded | `Cord inductance`, `eFuse model` (inrush), `OVLO window` (plug-in) |
| 5.7 | F1 drop at 1.0 A (e-load), cold | ≤ 55 mV (1.5 x 36.7 mΩ) | `Fuse resistance` |
| 5.8 | Rocker on/off 100 times. Before and after, measure the closed contact 4-wire at its tabs, harness unplugged, by the low-level method (EIA-364-23: ≤ 20 mV open circuit, ≤ 100 mA) | Contact **≤ 30 mΩ** before and after (E-Switch RA1 catalogue: 30 mΩ max, 10,000-cycle life). `+5V` comes up 100/100. At 5 mA wetting, 30 mΩ is 0.15 mV, so `RUN` follows `DC_FUSED` | `Rocker dry circuit` |

## Step 6: LED rail enable (no Pi; `LED_EN` from a lab source)

Use a lab supply at 5.00 V / 3 A. Remove only the J1.37 jumper (keep the J1.19/J1.23 grounds, so no clock reaches the chain) and drive J1 pin 37 to 3.3 V from a
lab supply or a lab GPIO (R13 is the series 1 kΩ). If anything below fails, **stop**:
it is a redesign item. Do not fit the Pi.

| # | Do | Pass | Closes |
|---|---|---|---|
| 6.1 | Raise `LED_EN`, 20 times, with no SPI | No LED lights; supply current rises < 0.32 A (64 x 5 mA); no eFuse trip; `+5V` ≥ 4.5 V. `LED_5V` 10-90 % rise about 0.95 ms. `LED_OE_N` falls only after `LED_5V` ≥ 4.605 V (simulated 1.78-3.05 ms after `LED_EN`), **then stays low while `LED_5V` is up** | `LED power-up state` |
| 6.2 | Lower `LED_EN` | `LED_OE_N` goes high within 0.61-0.83 µs [simulated]; `LED_5V` decays | — |

## Step 7: with the Pi (real GST12A05, firmware with the blank-frame contract)

| # | Do | Pass | Closes |
|---|---|---|---|
| 7.1 | Boot 10 times | No reset loop; `vcgencmd get_throttled` recorded | — |
| 7.1a | Board input current at 5.00 V with `LED_EN` low (LEDs off): Pi idle, then full CPU load (`stress-ng --cpu 4`) with `iperf3` Wi-Fi traffic, 2 min each. DC meter plus a scope current probe for peaks | Average ≤ **0.45 A** in both states (the model's host-and-logic budget). Peaks recorded. A higher average goes to hardware: the 4.5 V margins in 7.3 assume 0.45 A | `Host and logic current` |
| 7.2 | Walking LED and a 10 min animation at the cap (3/31), at the firmware SPI clock and at 10 MHz | 64/64 correct, no glitch. Scope TP3/TP4, U6 CKI/SDI and `LED_D16` (rank turn): edges cross 0.7/0.3 x VDD cleanly; ringing recorded | `SK9822 input levels`, `LED line drivers` |
| 7.3 | Lab supply at 4.75 V at the jack, Wi-Fi traffic, full white at the cap, 30 min | `+5V` (TP1) and `LED_5V` at the chain-end LED ≥ **4.5 V**; no reboot; `get_throttled` recorded (the Zero may not flag) | `Pi low voltage`, `GST12A05 output` (low corner) |
| 7.4 | Lab supply at 5.30 V, LEDs at the cap, 10 min | No flicker or colour error. 5.34-5.5 V cannot be held below the OVLO low corner and stays a residual | `LED supply window` (to 5.30 V only) |
| 7.5 | `i2cdetect`: 8 expanders at the `test_contract` addresses, plus the OLED. 1000-read soak. Scope TP6/TP7 at the farthest expander | 0 NACK; rise ≤ 1000 ns at 100 kHz (≤ 300 ns at 400 kHz, UM10204); VOL ≤ 0.4 V; OLED shows | `OLED pull-ups`, `OLED harness`, `J2 circuit 1` |
| 7.6 | 12 buttons, press and release | Idle high, one event per press | `Pi GPIO pull-ups` |
| 7.7 | Piece walk over all 64 squares, full start position plus one move | 64/64 detect and release; no neighbour false trigger; the `hall-magnet.json` record is written | (physical-evidence gate) |
| 7.8 | Closed case, 30 min at the cap (3/31 full white) with Wi-Fi traffic (can combine with 7.3/7.9); ambient logged. K-type thermocouples, Kapton-taped; IR only with tape or paint dots, because the print is IR-opaque and copper and mask emissivity differ. Points: (1) plate top and LED-pocket ceiling over a centre LED and over the LED nearest J4/U74; (2) PCB top at U74 and Q1, PCB bottom near J4; (3) the case boss nearest the Pi and the ledge by J4; (4) Pi SoC (`vcgencmd measure_temp`) and the Pi bay air. After cooling, check plate flatness with a straightedge and re-check screw torque. Record the filament make, type and TDS | Points 1 and 3, and the PCB wherever it touches the print: **≤ 45 °C and ≤ ambient + 20 K**. Points 2 and 4 recorded. No measurable change in flatness. The basis is PLA, HDT about 55 °C at 0.45 MPa (generic value; confirm from the filament TDS), less 10 K for creep under load. PETG or ASA may raise the limit once its TDS is cited | — (mechanical) |
| 7.9 | Pi in client mode to a fixed access point (or its hotspot to a fixed laptop), same room, line of sight, at 1/3/10 m, case closed vs open. Three runs each: RSSI (`iw dev wlan0 link`) and TCP throughput (`iperf3`, 30 s, both directions) | **TBD: the user sets the pass level.** Record the closed-minus-open loss | `Pi Wi-Fi` |

## Step 8: destructive (last, on a board declared sacrificial, or skipped)

| # | Do | Pass | Closes |
|---|---|---|---|
| 8.1 | Reversed 5.25 V plug, 10 s | `+5V` 0 V; D1 off; step 5.1 still passes afterwards | `eFuse model` (reverse) |
| 8.2 | Reversed 12 V adapter, 10 s | `+5V` 0 V; D1 off; steps 4.2, 5.1 and 5.5 still pass afterwards | `Reversed 12 V adapter` |
| 8.3 | Repeated current-limit retries: 2.5 A CC e-load for 60 s with `LED_EN` low, supply ≥ 3 A | Retry pulses about 110 ms apart, each ≤ 1.6 ms (record both); U74 case ≤ **100 °C**, steady after 60 s (thermocouple or IR; 25 °C margin to the 125 °C recommended TJ); afterwards 4.2, 5.1 and 5.5 still pass | `eFuse model` (heating) |
| 8.4 | Optional. Pi fitted with a **sacrificial SD card**, test firmware that overrides the cap and commands one full-white frame about 30 s after boot. Scope `+5V`, `LED_EN` and F1's voltage | Record which happens: `+5V` sags to about 3 V while U74 limits, or U74 opens within 1.6 ms and retries after 110 ms (the Pi browns out either way). Expect ≤ 0.025 A²s per event in F1 (4.7 %) [simulated]. The board recovers to a normal boot, and 5.7 still passes | `eFuse model` (system overload) |

## Not closed by bench

`EN at the surge clamp` is a part-change check: re-run the calculation if D1 changes. It
has no bench step.
