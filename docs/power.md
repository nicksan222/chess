# Power

## Purpose

Describe how the board is powered and where the current goes.

## No conversion on the board

A MEAN WELL GST40A05-P1J 5 V 6 A regulated supply feeds the barrel jack, and
that is the rail. There is no buck
converter, no inductor, no USB power negotiation and no battery. The 3.3 V the
expanders and the display need comes off the Raspberry Pi's own header, which
about 5 mA of load against a roughly 250 mA budget comfortably allows.

The whole power section is therefore six parts: the jack, a 5 A fuse in a holder,
a P6KE6.8A transient suppressor, a rocker switch, a 1000 µF bulk capacitor and a
10 µF rail capacitor.

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
array, so the rail is injected across all four quadrants instead of being fed
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
