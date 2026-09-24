# Firmware

This app contains the Raspberry Pi process and its Yocto build. The development
container includes the AArch64 linker and Rust target used by CI.

```sh
# Compile and link the complete Rust dependency graph for the Pi architecture.
just firmware-binary

# Validate or build the Yocto image; these commands require Docker.
just --justfile apps/firmware/justfile image-check
just --justfile apps/firmware/justfile image
```

The flashable files are written to `dist/firmware`.

## Runtime architecture

`src/runtime/` is the one event-driven application loop used by both the
executable and E2E tests. Hardware adapters publish typed physical observations
through `src/events/`; Tokio channels never escape that module. `src/harness.rs` starts
the same runtime without physical adapters and provides an acknowledged
`trigger` operation, so tests never race the event loop or duplicate production
behavior.

```sh
cargo test -p firmware --test e2e
```

Unit tests live beside their implementations in `src/`; `tests/` is reserved
for cross-module integration and E2E tests. The E2E cases live in `tests/e2e/`.
The default E2E run requires Docker: Rust
`testcontainers` starts real NetworkManager in an Ubuntu container and a pinned
Ubuntu QEMU VM. The VM loads two guest-kernel `mac80211_hwsim` radios; the Rust
probe uses the production `Connectivity` API to discover and join open/WPA
networks and start/stop a visible hotspot. In the same guest, `gpio-sim` creates
a 32-line Linux GPIO chip. The probe drives simulated input pulls and verifies
that the production `LinuxGpioReader` reads `/dev/gpiochip*` to deliver one
representative button's press and release to the firmware runtime. Existing
scripted GPIO cases cover all 12 mappings, bounce, initially held buttons,
and read failures deterministically. KVM accelerates the VM when available;
without `/dev/kvm`, QEMU uses slower software emulation. A cold VM image download is about 600 MB.
These tests verify Linux integration, **not** the Yocto image or Pi hardware.
The Linux GPIO reader is available to callers but is not yet wired into the
production executable's startup.

`src/connectivity/` owns typed, presentation-agnostic Wi-Fi control. Its
`Connectivity` API reports status, scans access points, manages the WPA
provisioning hotspot, and joins open or WPA Personal networks. Product code sees
validated SSIDs, redacted passphrases, and domain results rather than command
arguments or NetworkManager types. The implementation uses the maintained `nmrs` D-Bus
client; no shell or `nmcli` process is involved. The Yocto image
includes NetworkManager Wi-Fi support, `wpa-supplicant`, and `dnsmasq` for
NetworkManager's shared hotspot mode. Captive-portal presentation and menu
transition wiring remain separate consumers of this module.

`src/menu/definition.rs` is the single product menu definition. It composes the
headless `menu` crate's primitives into the Play, Connection, Pairing, Update,
and Settings submenus. Leaf requests are typed but deliberately immediate and
non-blocking until their external modules define completion and cancellation
behavior; the menu crate remains product-neutral and performs no operation.
Each request has one placeholder integration file under `src/menu/transitions/`,
so future module ownership has an explicit location without entering the menu
definition or runtime loop.

`src/hardware/buttons.rs` and `src/hardware/debounce.rs` own polling, active-low
translation, and mechanical debounce. Call `start_subscription` with a GPIO
reader, then await `on_message` for debounced pressed/released transitions.
`hardware::linux_gpio::LinuxGpioReader` requests inputs with internal pull-ups
on a caller-selected Linux GPIO chip; the button adapter interprets a low level
as pressed. The VM uses the external-bias constructor because `gpio-sim` drives
those levels via its separate sysfs interface. Callers do not inspect GPIO
levels.

`src/hardware/display/` constructs the externally maintained `ssd1306` crate's
buffered driver for the installed 128×64 OLED at address `0x3C`. It is
intentionally not attached to the runtime yet. Integration tests under
`tests/display/` capture the exact data packets emitted through I2C, decode the
transmitted frame, and compare it pixel-for-pixel with the externally maintained
`embedded-graphics-simulator`. Every display test writes a PNG result beside
the tests in `tests/display/screenshots/`.

The simulator verifies frame contents, not controller command semantics. Wokwi
can emulate an SSD1306 receiving real I2C traffic, but running this Raspberry Pi
firmware driver there requires a separate supported-microcontroller harness and
Wokwi CI credentials. No such harness is checked in because it would not execute
the production Pi I2C adapter.

The remaining hardware workers are not implemented yet. The board contract uses
polled TCA9554 input-port reads at eight addresses, not a GPIO sensor interrupt;
see [host acquisition](../../docs/host.md#reading-the-board). Reusable,
function-named GPIO identities and type-safe descriptors live in
`src/hardware/pins.rs`; OS-backed implementations live alongside them (currently
`src/hardware/linux_gpio.rs`). Unused header functions are deliberately absent.
`BoardPins` describes the three interfaces in the hardware wiring contract:
I2C for the shared bus, SPI for the LED chain, and direct GPIO button lines.
