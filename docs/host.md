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
| `/dev/i2c-1` | four MCP23017 expanders at 0x20-0x23, the OLED at 0x3C |
| `/dev/spidev0.0` | the SK9822 LED chain, through the level buffer |
| `/dev/gpiochip0` | the sensor interrupt and twelve panel buttons |

Suggested crates: `linux-embedded-hal` over `i2cdev`, `spidev` and `gpiocdev`;
`port-expander` for the MCP23017s; `ssd1306` with `embedded-graphics` for the
display. Note that `rppal`, the obvious first choice for Pi peripherals in Rust,
was retired by its author in July 2025, so the maintained character-device crates
are the better foundation for new work.

The LED frame needs no library. An SK9822 frame is a start frame of zero bytes,
four bytes per LED — brightness, then blue, green, red — and an end frame. Start
SPI at about 2 MHz, which is already over a thousand frames per second.

## Reading the board

The expanders raise an interrupt on change, so the Pi does not poll. Their INTA
pins are open-drain and wired together onto GPIO4, meaning any of the four can
pull the line low and the host reads all of them to find out which did.

Contact bounce is filtered in software, because the board carries no RC networks
on its 64 sense lines. On an interrupt: mask further interrupts, wait about 25 ms,
read the port registers — which also clears the expanders' interrupt latch — diff
against the last known state, then unmask. `crates/board-model`'s `Debouncer`
holds the state machine; it requires a square to read the same way for several
consecutive samples before believing it, so a chattering contact never settles.

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
