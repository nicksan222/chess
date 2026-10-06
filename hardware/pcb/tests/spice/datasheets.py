"""Device internals and limits quoted from manufacturer documents.

Each constant names its source. SPICE models build multi-pad devices from these
facts and the board's actual pad geometry/nets, never from the net names alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.electronics import sk9822

# E-Switch TL1105 series (2.28.2018). p24 specifications: contact resistance
# 100 mOhm max, insulation resistance 100 MOhm min. p25 drawing/schematic: leads
# 1-2 and 3-4 sit 6.50 mm apart and are internally connected; the dome bridges the
# pairs, whose leads sit 4.50 mm apart (holes +/-0.1 mm).
TL1105_CONTACT_OHMS_MAX = 0.1
TL1105_INSULATION_OHMS_MIN = 100e6
TL1105_STRAPPED_LEAD_PITCH_MM = 6.5
TL1105_BRIDGED_LEAD_PITCH_MM = 4.5
TL1105_LEAD_PITCH_TOLERANCE_MM = 0.3
# The internal strap is a single stamped terminal; its resistance is not specified,
# so it is modelled as the contact maximum, the most pessimistic stated value.
TL1105_STRAP_OHMS = TL1105_CONTACT_OHMS_MAX


@dataclass(frozen=True)
class Span:
    """A quantity's datasheet minimum and maximum (corners, not a nominal)."""

    low: float
    high: float


# --- Supply. The GST12A05-P1J spec (meanwell.com GST12A-SPEC.PDF) returns 404 and
# no mirror was found; the GST25B family sheet (2016-03-16) is used and the gap is
# verification ASSUMPTION "GST12A05 output": 5 V tolerance +-5.0 % (incl. setup,
# line, load regulation); overload 110-150 % rated power, hiccup; over-voltage
# 110-140 % rated voltage, zener clamp; 5-12 V cord UL2468 16 AWG 1000 +-50 mm.
PSU_RATED_VOLTS = 5.0
PSU_RATED_AMPS = 2.0  # GST12A05: 5 V 2 A (shared/components/power_supply.py).
PSU_VOLTS = Span(PSU_RATED_VOLTS * 0.95, PSU_RATED_VOLTS * 1.05)
PSU_OVERLOAD_FRACTION = Span(1.10, 1.50)
PSU_OVER_VOLTAGE_FRACTION = Span(1.10, 1.40)
PSU_RIPPLE_VOLTS_PP = 0.080  # GST25B05 ripple and noise (max.).
PSU_CORD_AWG = 16
PSU_CORD_METRES = Span(0.95, 1.05)
# Cord loop inductance [CALC], parallel wires: L = (mu0 / pi) acosh(s / d) per metre.
# UL2468 16 AWG zip cord, d 1.29 mm at about 2.9 mm centres: 0.58 uH/m, so 0.61 uH
# for 1.05 m; plus the 18 AWG harness pair and the jack, about 0.8 uH. No cord drawing
# is on file (verification ASSUMPTION "Cord inductance"): 0.5-1.5 uH is simulated.
PSU_CORD_HENRIES = (0.5e-6, 1.5e-6)

# --- Copper. IEC 60028 annealed copper: 1.7241e-8 ohm m and 0.00393 /K at 20 C.
# AWG diameter (ASTM B258): d = 0.127 mm * 92 ** ((36 - n) / 39). Conductor
# temperature corners 20-70 C (70 C = the supply family's working maximum).
COPPER_OHM_M_20C = 1.7241e-8
COPPER_TEMPCO_PER_K = 0.00393
CONDUCTOR_CELSIUS = Span(20.0, 70.0)

# --- Contacts (maximum stated; the minimum is not stated, so 0).
# Switchcraft 712A/722A sheet: 0.01 ohm initial, 0.02 ohm after humidity/durability.
JACK_CONTACT_OHMS = Span(0.0, 0.02)
# JST VH catalogue p2: 10 mOhm initial, 20 mOhm after test, per contact.
VH_CONTACT_OHMS = Span(0.0, 0.02)

# --- Fuses. Littelfuse 451/453 (2009-01-07) p58, 0453002 very fast: nominal cold
# resistance 0.0367 ohm, nominal melting I2t 0.530 A2s; opening 100 % >= 4 h,
# 200 % <= 5 s. Littelfuse 452/454 (rev 07/01/15), 0454002 Slo-Blo: 0.0625 ohm,
# 8.20 A2s; 200 % 1-60 s, 300 % 0.2-3 s. Littelfuse Fuseology Design Guide p3:
# keep a pulse's I2t <= 20 % of the nominal melting I2t (p5: 22 % for 100 000).
FUSE_0453002_COLD_OHMS = 0.0367
FUSE_0453002_MELTING_I2T = 0.530
FUSE_0454002_COLD_OHMS = 0.0625
FUSE_0454002_MELTING_I2T = 8.20
FUSE_PULSE_I2T_FRACTION = 0.20
# The sheets give nominal cold resistance only (10 % of rated current, 25 C), with no
# tolerance or hot value: the high corner allows 1.5 x (verification ASSUMPTION
# "Fuse resistance").
FUSE_RESISTANCE_FACTOR = Span(1.0, 1.5)

# --- Bulk capacitors. Rubycon ZLJ table: 10 V 560 uF 8 x 11.5, impedance 0.075 ohm
# max (100 kHz, 20 C), capacitance +-20 %. ESR minimum is not stated: 0 .. Z max.
ZLJ_560U_FARADS = Span(560e-6 * 0.8, 560e-6 * 1.2)
ZLJ_560U_ESR_OHMS = Span(0.0, 0.075)

# --- Loads and limits.
# Opsco SPC/SK9822-A Rev 01 (shared/electronics/sk9822.py): 18 mA per R/G/B output
# (the part name and §9; §10 lists Imax 17 mA, so 18 is the conservative choice);
# IDD 1 mA static; characterised at VDD 4.5-5.5 V; §8 VDD +3.7..+5.5 V (an
# operating range: 3.7 V is a floor, not an absolute rating; 5.5 V the maximum),
# VIN -0.3..VDD+0.3; chip supply 5.3 V maximum.
SK9822_CHANNEL_AMPS_MAX = sk9822.CHANNEL_AMPS_MAX
SK9822_STATIC_AMPS = sk9822.STATIC_AMPS
SK9822_VDD = Span(4.5, 5.5)
SK9822_VDD_MAX = sk9822.SUPPLY_ABSOLUTE_MAX_VOLTS
SK9822_VDD_RECOMMENDED_MAX = sk9822.SUPPLY_RECOMMENDED_MAX_VOLTS
# Vishay Si4403DDY (S17-0318-Rev A) LED switch Q1: RDS(on) 10.5 typ / 14.0 max at
# VGS -4.5 V, x 1.17 at 75 C (p3 "On-Resistance vs. Junction Temperature"); the
# switch dissipates milliwatts, so TJ is the 70 C ambient corner. No minimum is
# stated: 0 .. max, like the other unstated minimums (contacts, ESR).
LED_SWITCH_OHMS = Span(0.0, 0.0140 * 1.17)
# Raspberry Pi documentation (power-supplies.adoc): "below 4.63 V (+-5%)" low-voltage
# detection on models since B+ "except the Zero range"; Zero 2 W bare-board active
# typical 350 mA, recommended supply 2 A.
PI_LOW_VOLTAGE_VOLTS = 4.63
PI_ZERO_2_W_TYPICAL_AMPS = 0.350
# Pi plus logic, OLED and sensors: an allowance, not a datasheet figure
# (verification ASSUMPTION "Host and logic current").
LOGIC_ALLOWANCE_AMPS = 0.100
HOST_AND_LOGIC_AMPS = round(PI_ZERO_2_W_TYPICAL_AMPS + LOGIC_ALLOWANCE_AMPS, 6)

# TI SN74AHCT125 SCLS264R: §5.1 VCC -0.5..7 V; §5.2 VCC 4.5-5.5 V, VIH 2.0 V,
# VIL 0.8 V; §5.4 at VCC 4.5 V (-40..85 C): VOH 4.4 V at -50 uA, 3.8 V at -8 mA;
# VOL 0.1 V at 50 uA, 0.44 V at 8 mA.
AHCT125_VCC = Span(4.5, 5.5)
AHCT125_VCC_ABSOLUTE = Span(-0.5, 7.0)
AHCT125_VIH = 2.0
AHCT125_VIL = 0.8
AHCT125_IOZ_AMPS = 2.5e-6  # SCLS264R 6.5 off-state output leakage, max.
AHCT125_VOH_POINTS = ((50e-6, 4.4), (8e-3, 3.8))  # (|IOH| A, VOH V) at VCC 4.5
AHCT125_VOL_POINTS = ((50e-6, 0.1), (8e-3, 0.44))
AHCT125_VOH_TEST_VCC = 4.5
# The SK9822 sheet gives no input threshold: CMOS 0.7 x VDD / 0.3 x VDD is used
# (verification ASSUMPTION "SK9822 input levels").
SK9822_VIH_FRACTION = 0.7
SK9822_VIL_FRACTION = 0.3

# Raspberry Pi documentation (gpio-on-raspberry-pi.adoc, RP3A0 table): VIL <= 0.9 V,
# VIH >= 1.6 V, VOL <= 0.14 V and VOH >= 3.0 V at 2 mA (default 8 mA drive),
# pull-up 50-65 kOhm. The 3.3 V rail itself is taken as +-5 % (no Pi figure).
PI_GPIO_VIL = 0.9
PI_GPIO_VIH = 1.6
PI_GPIO_VOL_AT_2MA = 0.14
PI_GPIO_VOH_AT_2MA = 3.0
PI_GPIO_PULLUP_OHMS = Span(50e3, 65e3)
RAIL_3V3_VOLTS = Span(3.3 * 0.95, 3.3 * 1.05)

# TI TCA9554 SCPS233E §6.3 (VCC 3-5.5 V): P-port VIH 0.8 x VCC, VIL 0.2 x VCC;
# §6.5 IIL -100 uA max at VI = GND (sets the strongest pull-up), IIH 1 uA; the
# pull-up is 100 kOhm typical (§8.3), no maximum stated.
TCA9554_VIH_FRACTION = 0.8
TCA9554_VIL_FRACTION = 0.2
TCA9554_PULLUP_AMPS_MAX = 100e-6
TCA9554_PULLUP_OHMS_TYPICAL = 100e3
TCA9554_INPUT_LEAKAGE_AMPS = 1e-6
# TI DRV5032 SLVSDC7H: FC is open drain (Table 4-1); §6.5 VOL 0.3 V max at 1 mA,
# off-state leakage IOZ 100 nA max.
DRV5032_VOL_AT_1MA = 0.3
DRV5032_LEAKAGE_AMPS = 100e-9

# --- S4b input protection. TI TPS25947 SLVSFC9C (rev May 2026), TPS259474ARPW:
# 6.5 RON 28.2 mOhm typ (25 C), 45 mOhm max (-40..125 C); OVLO and EN/UVLO rising
# 1.183-1.223 V, falling 1.076-1.116 V; OVLO pin leakage +-0.1 uA; dVdt charging
# current 0.81-3.82 uA (2.21 typ) with CdVdt(pF) = 2000 / SR(V/ms) at typ (7.3.5.1);
# ILIM at RILM 1.65 kOhm 1.800-2.200 A; ITIMER discharge 1.2-2.5 uA through
# dV 1.286-1.741 V; OVLO response 1.2 us typ. 6.1: IN down to -15 V; 7.3.1/8.2:
# IN-referred pins need >= 350 kOhm so reverse-polarity pin current stays < 10 uA.
EFUSE_RON_OHMS = Span(0.0, 0.045)
EFUSE_RON_TYPICAL_OHMS = 0.0282
EFUSE_THRESHOLD_RISING_VOLTS = Span(1.183, 1.223)
EFUSE_THRESHOLD_FALLING_VOLTS = Span(1.076, 1.116)
EFUSE_OVLO_LEAKAGE_AMPS = 0.1e-6
EFUSE_DVDT_AMPS = Span(0.81e-6, 3.82e-6)
EFUSE_DVDT_TYPICAL_AMPS = 2.21e-6
EFUSE_DVDT_PF_VOLTS_PER_MS = 2000.0
EFUSE_ILIM_AMPS_AT_1K65 = Span(1.800, 2.200)
EFUSE_ITIMER_AMPS = Span(1.2e-6, 2.5e-6)
EFUSE_ITIMER_DELTA_VOLTS = Span(1.286, 1.741)
# TPS259474A overcurrent (SLVSFC9C §6.5/§6.6, §7.3.5.2-4): fast-trip ISC = ISCGain
# x ILIM, 201 % typical (no limits published); ITIMER pull-up 15 kOhm; auto-retry
# tRST 110 ms typical after a breaker or thermal fault.
EFUSE_ISC_RATIO = 2.01
EFUSE_ITIMER_PULLUP_OHMS = 15e3
EFUSE_RETRY_S = 0.110
EFUSE_IN_MIN_VOLTS = -15.0
EFUSE_REVERSE_PIN_AMPS_MAX = 10e-6
# Littelfuse SMBJ (rev 06/03/20) p2 row SMBJ12CA (user decision D2): VR 12.0 V, VBR
# 13.30-14.70 V at IT 1 mA, VC 19.9 V at IPP 30.2 A (bidirectional: same both ways).
TVS_STANDOFF_VOLTS = 12.0
TVS_BREAKDOWN_VOLTS = Span(13.30, 14.70)
TVS_TEST_AMPS = 1e-3
TVS_CLAMP_VOLTS = 19.9
# Resistor tolerances: Yageo RC 1 % (F), RT 0.1 % (B).
RESISTOR_TOLERANCE = {"RC": 0.01, "RT": 0.001}
# Yageo CC...K X7R MLCC: K = +-10 % capacitance.
MLCC_X7R_TOLERANCE = 0.10

# --- S5 buses. PCBWay "8-layers PCB, Regular, 1.6MM, 1 oz, 70 % residual copper"
# (pcbway.com/multi-layer-laminated-structure.html), thickness after lamination
# (mm, Dk), F.Cu to B.Cu; the repo records no stackup (verification ASSUMPTION
# "Stackup"). Planes: In1 GND, In2 +5V, In3 +3V3, In6 LED_5V (native.add_power_planes).
STACKUP_DIELECTRICS = (
    (0.1195, 4.45),
    (0.23, 4.6),
    (0.175, 4.74),
    (0.23, 4.6),
    (0.175, 4.74),
    (0.23, 4.6),
    (0.1195, 4.45),
)
STACKUP_COPPER_MM = 0.035
