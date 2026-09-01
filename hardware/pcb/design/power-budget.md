# Revision C power budget

The input is intentionally limited by a 5 V / 2 A Mean Well GST12A05-P1J supply
and a 2 A time-delay fuse. This keeps the Same Sky PJ-102A at or below its 2.5 A
continuous rating even under a downstream fault.

## Design envelope

| Load | Bring-up allowance |
|---|---:|
| Raspberry Pi Zero 2 W, CPU/Wi-Fi transient | 1.20 A |
| Four MCP23017s, 64 Hall sensors, OLED, buffer | 0.15 A |
| SK9822 idle/controller current | 0.10 A |
| Wiring, tolerance, and transient reserve | 0.20 A |
| Available average RGB channel current | 0.35 A |
| **Total** | **2.00 A** |

A 64-pixel chain can approach 3.84 A at 20 mA per red, green, and blue channel.
Full-brightness white is therefore forbidden. Firmware must set the SK9822
five-bit global-brightness field to **no more than 3/31** before displaying any
frame. At a nominal linear 20 mA/channel this limits full-white channel current
to about 0.37 A. Application RGB values may reduce brightness further, but may
not raise this hardware-wide ceiling.

The cap must be applied by the lowest-level LED driver during initialization,
not by UI convention. Bring-up must verify the limit with a current meter and
must stress CPU, Wi-Fi, OLED, and all LEDs simultaneously while monitoring the
Pi 5 V rail for undervoltage.

## Protection intent

- F1 protects the connector and wiring from sustained over-current; it is not a
  precision current limiter.
- D1 is a transient and reverse-polarity crowbar. SMBJ6.0A does not provide
  precision 5 V over-voltage protection, so only the approved regulated supply
  may be connected.
- Production approval still requires measured input current, far-corner 5 V
  voltage, fuse behavior, and Pi undervoltage results on a physical board.
