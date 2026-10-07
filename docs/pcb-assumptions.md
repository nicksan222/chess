# PCB engineering assumptions

These retained assumptions need reassessment against the current board. They are not validation evidence or fabrication approval. No prototype measurements are recorded.

## PTH copper rings

0.4 mm annulus (rules.THT_ANNULAR_RING_MM) on JST VH (J4), TL1105, Sullins and Rubycon pads: their drawings give holes only

## CAP_560U drill

0.9 mm: Rubycon ZLJ lead φ0.6 plus the repository's 0.3 mm THT allowance; no recommended hole is published

## OLED harness

J2 pins GND/3V3/SCL/SDA are soldered to MC242GW pins 1–4; optional RES is left open for onboard RC reset. The approved module supports 3.3 V per its supplier specification; omit its upright header.

## Jack/plug fit

Switchcraft 722A split Ø0.080 in centre pin is made for the 5.5 x 2.1 plug (EDG41 p134: S760, bore 2.03-2.13; plf6: pin .075-.077 in, insertion <= 3 lb, withdrawal >= 4 oz, contact <= 0.01 ohm initial, 0.02 ohm after humidity and durability); the GST18A05-P1J plug itself is not dimensioned on file; bench fit/retention/contact check

## J4 back offset

B4PS-VH body taken to start 1.0 mm behind the hole row; JST VH p3/p4 do not dimension it

## J2 circuit 1

SH side-entry land p1 has no circuit-1 mark; pin 1 at -X with the tabs at -Y is inferred from the p2 top view

## Harness parts

18 AWG wire (Alpha Wire 3055, four colour suffixes), 28 AWG PTFE wire (Alpha Wire 2842/7, 0.69 mm OD for the SSH contact, four colours) and TE 2-520275-2 FASTON (0.81 mm tab) are from distributor listings; manufacturing confirms the MPNs (the RA1 tab is 4.80 x 0.80 mm, E-Switch RA1 catalog drawing 11/2/2022, which the 0.81 mm FASTON fits)

## Pi Wi-Fi

Pi Zero 2 W PCB antenna (inferred, board x 118..138.5, y -54.5..-48.5) sits 11 mm under the full-plane 8-layer board in a printed case; no copper window (the rank-3 LED chain crosses that area); bench: hotspot RSSI/throughput at 1/3/10 m, case closed vs open

## MLCC lands

the 0603 MLCCs (100 nF, 10 nF, 1 nF, 1 uF) are Yageo class DA, 1.6 +-0.1 x 0.8 +-0.1 (CC X7R V.18 Table 3), matching the Murata ±0.10 lands; CAP_10U (0805 X5R) uses the 2.0x1.25 ±0.20 land, its Yageo X5R thickness class not read (sheet not obtained)

## Pi GPIO pull-ups

panel buttons rely on the Pi's internal pull-up, requested by firmware (apps/firmware/src/hardware/linux_gpio.rs Bias::PullUp); no board resistor

## GST18A05 output

GST18A-SPEC 2026-04-03 gives 5 V +-5 %, 80 mV p-p ripple, 3 A rated, overload 110-150 % hiccup, OVP 110-140 %, 16 AWG 1.2 m cord; bench: no-load and 2 A output voltage of the supplied unit (the board retains its 2 A budget)

## eFuse model

U74 (TPS259474ARPWR) is simulated from SLVSFC9C tables, no vendor model [BEH], with OVLO hysteresis and separate EN/OVLO thresholds, start-up limiting at ILIM, the ITIMER breaker (C143 1 nF: 1.286-1.741 V x 0.9-1.1 nF / 1.2-2.5 uA = 0.46-1.6 ms), the fast trip at ISC (2.01 x ILIM, typical only: no limits published) into limiting, and the 110 ms auto-retry; which branch a 4 A overload takes (fast trip, or the breaker) depends on that unpublished ISC spread and tSC is specified only above 3 x ILIM, so both branches are tested and bounded; thermal shutdown is not simulated (no transient thermal impedance published), so how long U74 limits before TSD is a bench item; reversed plug: 5.25 V / 604k = 8.7 uA per pin with an ideal clamp (< 10 uA, 8.2), the simulated figure uses a generic pin clamp; bench: scope inrush at hot plug and switch-on, OVLO trip with a lab supply, reversed plug, breaker trip at full white

## LED power-up state

SK9822-A Rev 01 p3 says 'default on electric lights'; distributors say no illumination at power-on. LED_5V stays off until LED_EN (S6), but if the chain wakes lit, enabling it pulls about 4 A: U74 either fast-trips and limits at 1.8 A (+5V about 3 V) or passes it until its breaker opens about 1.6 ms later (+5V then decays) [BEH], both before U5 can clock a blank frame (U75 holds U5 off until LED_5V is up, S6b H6): the Pi resets, R14 turns the rail off, the Pi reboots and enables again, a boot loop. PRE-ORDER bench test, before any LED purchase for assembly: a loose SK9822-A on a current-limited lab supply, DI and CI held low through 10 kOhm as on the board (S6d; the SK9822-A gives no input leakage, and 10 kOhm keeps DI/CI under 0.3 V for up to 30 uA of U5 plus U6 leakage, U5's IOZ being 2.5 uA max), VDD ramped 0 -> 5 V twenty times with no clock or data; pass = no LED lights and each LED draws < 5 mA before its first frame; then, on the board, enable an uninitialised chain and scope +5V, LED_5V and U74 current

## Host and logic current

+5V carries the Pi plus logic as 0.45 A: the Pi Zero 2 W's 'typical bare-board active' 350 mA (Raspberry Pi power-supplies documentation; no maximum is published) plus a 100 mA allowance for the OLED, U5, U75, the eight TCA9554 and the 64 DRV5032, not a datasheet sum; Pi peaks above typical (CPU load, Wi-Fi) are not covered; bench: board input current with LEDs off, idle and at full CPU load with Wi-Fi

## OVLO window

OVLO trips at 5.34-5.66 V (604k/169k 0.1 %, VOV(R) 1.183-1.223 V, +-0.1 uA) and restarts below 4.85-5.17 V (VOV(F)); C144 10 nF stops plug-in rings tripping it (without it a +5 % supply locks out at the low corner [BEH]); an overshoot above 5.34 V for about 1 ms or more that settles above 4.85 V still locks out until replugged; a supply failing into 5.5-5.66 V stays on and stresses the LEDs (VDD abs max 5.5 V); after any trip a supply at +5 % never restarts and 5.0 V restarts only at the high VOV(F) corner [BEH], so the product must be unplugged and replugged after an over-voltage event; bench: trip/restart points, plug-in with the real adapter

## LED supply window

SK9822-A Rev 01 lists the chip supply at 5.0 V typical, 5.3 V maximum (VDD range to 5.5 V): the PSU's +5 % (5.25 V) is inside it, but the OVLO trip (5.34-5.66 V) sits above 5.3 V and up to 0.16 V above the 5.5 V maximum at its latest corner; a supply between 5.3 V and the trip runs the LEDs beyond their recommended supply; bench: LED behaviour at 5.3-5.5 V

## OVLO filter

C144 delays OVLO: a running supply stepping to 6 V / 7 V trips after 1.72 / 0.65 ms; the rail peaks at 5.99 / 6.03 V and stays above 5.5 V for 10.5 / 10.0 ms with only the LEDs' static load (bulk capacitors hold it) [BEH]; D1 (VBR >= 13.3 V) does not clamp 6-7 V; bench: step a lab supply 5 -> 6 V under the idle board

## Fuse resistance

Littelfuse 451/453 gives F1's nominal cold resistance only (0.0367 ohm at 10 % of rated current, 25 C): the supply corner allows 1.5 x for tolerance and self-heating; bench: F1 voltage drop at 1 A

## Reversed 12 V adapter

D1 SMBJ12CA (user decision D2): a reversed 12 V adapter keeps the rail off (U74 IN -15 V rating, D1 off below 13.3 V) but pushes about 12 V / 604k = 20 uA into EN and OVLO with an ideal clamp, above TI's 10 uA (SLVSFC9C 8.2); surges clamp at VC 19.9 V (IN max 28 V); bench: reversed 12 V adapter, U74 still works afterwards

## EN at the surge clamp

at D1's 19.9 V clamp (SMBJ12CA VC at IPP) R6/R7 put U74 EN at 19.9 x 261k / 865k = 6.0 V, 0.5 V under its 6.5 V absolute maximum (SLVSFC9C 6.1); a clamp above about 21.5 V (a part swap, or a surge past IPP) would exceed it; bench: none, a part-change check

## LED moisture sensitivity

SK9822-A Rev 01 p1: MSL 5a (24 h floor life after opening the dry pack, then bake per J-STD-033); 64 LEDs on one panel make floor life an assembly constraint; U74 TPS259474ARPWR is MSL 2; the assembler confirms dry-pack handling and bake

## Cord inductance

supply cord and harness loop 0.5-1.5 uH (parallel-wire estimate about 0.8 uH for the 1 m UL2468 16 AWG cord; no cord drawing on file); bench: scope DC_FUSED at plug-in

## Rocker dry circuit

E-Switch RA1 (11.3.2022) rates RA11131100 at 10 A 125 VAC with 30 mOhm contact resistance max but gives no minimum switching current or dry-circuit rating: the rocker switches DC_FUSED onto RUN with a 1 kOhm wetting load (about 5 mA, 28 mW at 5.25 V); bench: RUN voltage and contact resistance over repeated switching

## U74 fine-pitch DRC

Lead-approved scoped rule (generated chess-board.kicad_dru): 0.16 mm clearance and 0.20 mm tracks only for U74 pads and escape copper inside its courtyard (RPW0010A 0.2 mm pad gaps), board 0.30/0.31 elsewhere; above PCBWay's 1 oz outer 5/6 mil (rules.PCBWAY_MIN_*); fab confirms at order

## Pi low voltage

Worst corner (PSU -5 %, end-of-life contacts, 70 C, fuse 1.5 x, Q1 hot) gives 4.525 V at the Pi header and 4.518 V at the farthest LED (Q1 drops 6.5 mV) [BEH]: SK9822/AHCT125 4.5 V met, the 4.63 V Pi warning level (not detected on the Zero range) not; bench: vcgencmd get_throttled with a low supply at the approved LED cap

## SK9822 input levels

Opsco SK9822-A Rev 01 gives no VIH/VIL: SPICE uses CMOS 0.7/0.3 x VDD for the AHCT125-driven data and clock; bench: chain test at the SPI clock

## Stackup

PCBWay 8-layer regular 1.6 mm (1 oz, 2116/7628 prepreg, Dk 4.45-4.74) from the fab's published table, +10 % capacitance: I2C load and LED line impedance (spice/bus_lines.py); fab confirms the stackup at order

## OLED pull-ups

The Pi's 1.8 kΩ and MC242GW's documented 4.7 kΩ (R2/R3 on its supplier schematic) give 1.30 kΩ nominal and 2.23 mA at 0.4 V; PCB R1/R2 remain omitted. Module input 10 pF and harness 50 pF/m remain estimates. Verify the delivered variant's resistors before fitting, then measure populated bus rise time and low voltage at the retained 100 kHz setting.

## LED line drivers

AHCT125 output 75/43 Ohm (SCLS264R VOH/VOL slopes) and 1-3 ns edges (not specified); SK9822 input 5 pF, output 25-100 Ohm with 1-3 ns edges (not in the Opsco sheet; R10-R12 terminate the In4 rank-turn data hops for that range); bench: scope U6 CKI/SDI and LED_D16 at the SPI clock

## Via plating

0.018 mm hole-wall copper (PCBWay standard 18-25 um, per the manufacturing review) for via ampacity; the fab's plating certificate confirms at order

## CAD CASE_ROCKER_BAY_DEPTH_MM

Rocker body and tabs reach 18.5 +/- 1.0 mm behind the panel (E-Switch RA1 sheet p2); the two TE 2-520275-2 receptacles and wire exit are not drawn. 50.5 mm reserved.

## CAD CASE_JACK_BAY_DEPTH_MM

722A body and lugs reach 15.3 mm behind the panel (drawing 20.8 - 5.46); 30 mm reserved for the soldered 18 AWG wires and their bend.

## CAD PI_SD_SOCKET_ON_PI_MM

microSD socket centre measured from the rendered RP-008358-DS-1 view; the drawing does not dimension it.

## CAD PI_SD_SOCKET_HEIGHT_MM

microSD socket height on the Pi Zero 2 W assumed (1.4 mm); sets the slot height.
