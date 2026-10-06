# Harness wiring

Generated from `hardware/shared/electronics/harness.py`; do not edit.
Cavity numbers are JST's: cavity k mates header circuit k.

## Power entry

| Header | Cavity | Net | Wire | Far end | Terminal | Attach |
|---|---|---|---|---|---|---|
| J4 | 1 | DC_IN | red 18 AWG 200 mm | Switchcraft 722A | CENTER PIN | solder lug |
| J4 | 2 | GND | black 18 AWG 200 mm | Switchcraft 722A | SLEEVE | solder lug |
| J4 | 3 | DC_FUSED | orange 18 AWG 200 mm | E-Switch RA11131100 | either tab | FASTON 2-520275-2 |
| J4 | 4 | RUN | white 18 AWG 200 mm | E-Switch RA11131100 | other tab | FASTON 2-520275-2 |

- 1 JST VHR-4N: 4-pin VH receptacle housing for the power harness (bought: each)
- 4 JST SVH-21T-P1.1: VH crimp contact, AWG 22-18, insulation 1.7-3.0 mm (bought: each)
- 2 TE Connectivity 2-520275-2: FASTON .187 insulated receptacle, 22-18 AWG (bought: each)
- 1 x 200 mm Alpha Wire 3055 RD005: 18 AWG UL1007 wire, red (bought: 100 ft spool)
- 1 x 200 mm Alpha Wire 3055 BK005: 18 AWG UL1007 wire, black (bought: 100 ft spool)
- 1 x 200 mm Alpha Wire 3055 OR005: 18 AWG UL1007 wire, orange (bought: 100 ft spool)
- 1 x 200 mm Alpha Wire 3055 WH005: 18 AWG UL1007 wire, white (bought: 100 ft spool)

## OLED

| Header | Cavity | Net | Wire | Far end | Terminal | Attach |
|---|---|---|---|---|---|---|
| J2 | 1 | GND | black 28 AWG 90 mm | AZ-Delivery A 1-9 | GND | solder to pad |
| J2 | 2 | +3V3 | red 28 AWG 90 mm | AZ-Delivery A 1-9 | VCC | solder to pad |
| J2 | 3 | I2C_SCL | yellow 28 AWG 90 mm | AZ-Delivery A 1-9 | SCL | solder to pad |
| J2 | 4 | I2C_SDA | blue 28 AWG 90 mm | AZ-Delivery A 1-9 | SDA | solder to pad |

- 1 JST SHR-04V-S-B: 4-pin SH receptacle housing for the OLED harness (bought: each)
- 4 JST SSH-003T-P0.2-H: SH crimp contact, AWG 32-28, insulation 0.4-0.8 mm (bought: each)
- 1 x 90 mm Alpha Wire 2842/7 BK005: 28 AWG PTFE wire, black (bought: 100 ft spool)
- 1 x 90 mm Alpha Wire 2842/7 RD005: 28 AWG PTFE wire, red (bought: 100 ft spool)
- 1 x 90 mm Alpha Wire 2842/7 YL005: 28 AWG PTFE wire, yellow (bought: 100 ft spool)
- 1 x 90 mm Alpha Wire 2842/7 BL005: 28 AWG PTFE wire, blue (bought: 100 ft spool)
