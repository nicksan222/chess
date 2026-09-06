# Host

## Purpose

Describe the software that runs on the Raspberry Pi: how it reaches the hardware,
how the board joins a network, and what the player sees when something is wrong.

## One binary

The Pi is the only processor, so the whole product is one Rust program in
`apps/firmware`, built for `aarch64-unknown-linux-gnu`. The app also owns the
Yocto definition for its flashable Linux system.

It reaches the hardware through Linux character devices:

| Device | Carries |
|---|---|
| `/dev/i2c-1` | eight TCA9554 expanders at 0x20-0x27, the OLED at 0x3C |
| `/dev/spidev0.0` | the SK9822 LED chain, through the level buffer |
| `/dev/gpiochip0` | twelve panel buttons (unchanged GPIO wiring) |

Suggested crates: `linux-embedded-hal` over `i2cdev`, `spidev` and `gpiocdev`.
The standalone SSD1306 driver exists, but it is not connected to a physical I2C
adapter or the runtime yet; the TCA9554 acquisition worker is also pending. Note
that `rppal`, the obvious first choice for Pi peripherals in Rust, was retired by
its author in July 2025, so the maintained character-device crates are the better
foundation for new work.

`apps/firmware/src/hardware/pins/` contains hand-maintained, function-named `GPIO`
descriptors for every connected Raspberry Pi line. They record host identity,
allowed direction and active-low behavior so drivers do not duplicate board
knowledge. PCB-to-Rust generation was deliberately removed; coordinate changes
to these descriptors with `hardware/shared/wiring.py` and the native PCB host
connections.

The LED frame needs no library. An SK9822 frame is a start frame of zero bytes,
four bytes per LED — brightness, then blue, green, red — and an end frame. Start
SPI at about 2 MHz, which is already over a thousand frames per second.

## Reading the board

The D-PROTOTYPE board **polls** eight TCA9554DWRs. Their INT outputs are
explicitly no-connect, and Pi header pin 7 (GPIO4) is unused. There is no shared
sensor IRQ, IRQ pull-up, or IRQ test point.

At startup, and after any detected expander power loss, write Configuration
register **0x03 = 0xFF** (all eight pins inputs) and Polarity Inversion register
**0x02 = 0x00**. Read Input Port register **0x00** using a command write followed
by a repeated-start byte read. There is one 8-bit port, not two; Output Port
register 0x01 must not be used to acquire sensors. Do not apply a different
expander family's register map or enable outputs against the open-drain sensors.

Scan addresses 0x20–0x27 in order; map P0–P7 with the bank contract in
`hardware/shared/hall_banks.py` (four files by two ranks; left half P0–P3,
right half P4–P7). LOW means occupied. Eight sequential reads are **not an atomic
64-square capture**. Begin at 100 kHz I²C, aiming for a complete scan every
25 ms; this is a starting software target, not measured scheduling performance.
A command/read uses about 36 bus clocks, so eight banks take about 2.88 ms at
100 kHz, before Linux and OLED traffic. Serialize access with the OLED and retain
per-bank timestamps. Failed reads mean unknown/stale data, never an empty square;
report faults and reconcile the full board after recovery. A stuck-low target
can block the entire shared bus.

The DRV5032FC samples internally at 20 Hz typical (27–75 ms period). Faster
polling cannot recover unobserved magnetic transitions. Require stable readings
across successive complete scans before reporting a move, with the final
filter/latency chosen by prototype testing. This is magnetic/noise filtering,
not mechanical-contact debounce. Button debounce remains a separate GPIO concern.

Each TCA9554 input has a **100 kΩ typical** internal pull-up to 3.3 V; this is
not a precision or guaranteed maximum resistance. No external Hall pull-ups or
RC filters are fitted. As an illustrative lumped estimate, 100 kΩ and 50 pF give
5 µs RC and about 6 µs to 0.7 VCC. Actual trace/input capacitance, leakage,
weak-pull-up variation, slow edges, and LED-coupled noise need measurement at the
furthest channels; a typical estimate is not a worst-case guarantee. Keep the
DRV5032FC 3.3 V open-drain output and local 100 nF bypassing.

SDA/SCL pull-ups R1/R2 remain 4.7 kΩ to 3.3 V. Include the Pi's approximately
1.8 kΩ pull-ups and any display-module pulls when measuring the parallel load
(4.7 kΩ || 1.8 kΩ is about 1.30 kΩ). Verify sink VOL and rise time against the
complete nine-target bus capacitance, particularly before attempting 400 kHz.
The retained stackup and local Hall routes do not prove signal integrity.

These are the contract for future hardware workers, not an implemented driver
or evidence of physical operation.

## Joining a WiFi network

WPS is not an option. Raspberry Pi OS has used NetworkManager since Bookworm,
NetworkManager has no client-side WPS enrollment, and WPA3 dropped WPS entirely.

Use access-point provisioning instead. On boot with no known network:

1. Raise a hotspot: `nmcli device wifi hotspot ifname wlan0 ssid chess-XXXX`.
   This needs `dnsmasq-base` installed, because that is what NetworkManager runs
   internally for a shared connection.
2. Advertise the portal with DHCP option 114, per RFC 8910, so phones open it
   automatically.
3. Serve a page listing scanned networks, take a passphrase, and write it as an
   `.nmconnection` profile.
4. Drop the hotspot and join.

A single radio cannot be an access point and a client at the same time, so
provisioning is strictly sequential. The player types the passphrase on their own
phone keyboard, which is why the board needs no on-device text entry.

## What the player sees

The OLED shows boot state, the hotspot name during setup, the IP address once
joined, and error text. Being a graphical display it can also render a QR code for
the setup page, which a character LCD could not.

Twelve buttons, all the same part: five directions, OK, RESET, PASS and F1 to F5.
A long press on RESET forgets the network and re-enters setup. Remapping any of
them is a change here and nowhere else, because they are wired straight to GPIO
rather than through an expander.

The 64 board LEDs are a second status surface — a red sweep for a fault, an amber
pulse for no network — and are useful precisely when the display is the thing that
has failed.

## Staying alive

There is no second processor to notice a hung kernel. Enable the Pi's own SoC
watchdog through systemd's `RuntimeWatchdogSec`. If LED animation ever looks
uneven, put the render thread on `SCHED_FIFO`; because the LED protocol is
clocked, scheduler jitter makes a frame late rather than corrupt.

## TODO

The systemd-supervised process and Yocto packaging exist. Physical I/O, display,
network provisioning, and game coordination are not implemented yet.
