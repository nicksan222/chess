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
