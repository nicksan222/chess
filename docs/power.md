# Power

## Purpose

Document the future battery and power architecture.

## Revision-A prototype

The prototype is battery-powered from six removable AA NiMH cells. A 5 A fuse,
latching switch, input TVS, and Pololu D36V50F5 step-down module produce the
5 V controller and LED rail. Charging is deliberately external: cells must be
removed and charged in a certified NiMH charger.

The 64 WS2812B LEDs have a theoretical unrestricted full-white load of 3.84 A.
The 5 A regulator leaves controller margin, and 1000 µF of bulk capacitance is
specified at the LED rail. Normal firmware should cap aggregate brightness, and
the physical harness must inject 5 V and ground at every LED row rather than
passing all power through the complete chain.

GP26/ADC0 monitors the switched battery through a 100 kΩ/39 kΩ divider and a
10 kΩ fault-current limiting resistor. An 8.7 V pack maximum produces about
2.44 V at the ADC.

## TODO

Load-test the complete power path, measure regulator temperature and far-end LED
voltage, establish low-battery policy from measured NiMH discharge behavior,
and validate fuse, switch, connector, and conductor ratings before fabrication.
