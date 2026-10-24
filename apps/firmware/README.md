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
executable and the runtime tests. Hardware adapters publish typed physical observations
through `src/events/`; Tokio channels never escape that module. `src/harness.rs` starts
the same runtime without physical adapters and provides an acknowledged
`trigger` operation, so tests never race the event loop or duplicate production
behavior.

`just --justfile apps/firmware/justfile test` runs unit tests and `tests/`: the
production runtime with injected hardware (`tests/runtime/`), display rendering
(`tests/display/`) and the command line. It needs no Docker or hardware. Scripted
GPIO cases cover all 12 button mappings, bounce, initially held buttons and read
failures. Product logic above the Linux adapters is tested against in-memory
fakes; the adapters themselves (NetworkManager through `nmrs`, GPIO through
`gpiocdev`) run only on the board, where real Wi-Fi, GPIO and display behaviour is
validated.
The executable starts all twelve button pollers on `/dev/gpiochip0` with internal
pull-ups. Opening logs the chip path and pull-up configuration, then reports the
number of initialized inputs on success. If a line cannot be acquired or read,
it logs an error and returns the chip path, button name, GPIO number and underlying
cause; startup fails so systemd can restart the process. `ButtonPanel` owns the
pollers and stops them when dropped. Its injected-reader constructor exercises the
same panel startup and runtime delivery without GPIO hardware.

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
Each request is handled by a transition under `src/menu/transitions/`. A
transition is defined entirely in its own file by implementing the `Transition`
trait: the request it handles and, for a blocking item, the escape action that
cancels it; its `Settings` (`Default` is the network-free value tests use,
`device()` the product's); its `Status` for the snapshot; and `start` and
`cancel`. One line in the `transitions!` registry in `mod.rs` wires it in,
generating its `Config` field, its `Snapshot::transitions` field and its
dispatch. Every request has a transition; those whose integration does not
exist yet are placeholders that finish immediately. Tests require a transition
for every menu request and check each against its menu item.

The kind follows from the menu item and what the transition reports. A
blocking item holds input until the transition reports `finish`; escape calls
`cancel`. A plain item stays free while a background transition reports
`progress` and `finish`, or an immediate one finishes inside `start`. Reports
are `TransitionEvent`s, which the runtime loop receives alongside hardware
events; one generic rule releases the menu when the request blocking it
finishes. `Snapshot::blocking` names the operation holding input. Tests drive
the real menu, inject reports with `FirmwareHarness::report` as they inject
hardware with `trigger`, and wait for background results with `until`.

`src/updater/` owns the local firmware and its updates, independent of menus
and displays. `installed` names the running firmware and its Cargo version,
used by `--version`, the startup log and the user agent. `Updater::check`
first runs preflight checks, cheapest first, so a failure names its cause: the
system clock must be set (`ClockNotSet`), the release host must resolve
(`Offline`) and accept a connection (`Unreachable`). It then asks the GitHub
Releases API for this repository's latest stable release over HTTPS and
compares its `v<version>` tag with the installed version: `NoRelease` (404),
`UpToDate` or `Available(Release)`. A failing service is `ServiceDown`, an
exhausted quota `RateLimited`, and other failures keep their cause chain. TLS uses `rustls` on `ring` with the image's `ca-certificates`, so it
needs a synchronised clock. Installing an update is not implemented.

The Check for Updates transition only runs that check and presents it as
`Snapshot::transitions.update`: `Checking`, then the result, `Disabled` or
`Failed`. No button is bound to escape yet, so a check ends with its result or
a 15 s timeout.

`src/hardware/buttons.rs` and `src/hardware/debounce.rs` own polling, active-low
translation, and mechanical debounce. Call `start_subscription` with a GPIO
reader, then await `on_message` for debounced pressed/released transitions.
`start_subscription` uses the default `ButtonTuning`; `ButtonPanel::open` and
`start` take the tuning the executable loaded.
`hardware::linux_gpio::LinuxGpioReader` requests inputs with internal pull-ups
on a caller-selected Linux GPIO chip; the button adapter interprets a low level
as pressed. `with_external_bias` leaves line bias to the board instead of
requesting an internal pull-up. Callers do not inspect GPIO levels.

`src/hardware/display/` constructs a buffered SSD1309 driver for the installed MC242GW
2.42-inch 128×64 OLED at address `0x3C`. The four-wire I²C module supplies
power-on reset; allow 200 ms of stable power before initialization. Construction
and drawing perform no I/O; initialize, clear, flush and power retain the same API. It is
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

## Tuning

`src/tuning/` holds values worth adjusting on a prototype without rebuilding,
currently the button poll interval and debounce. One `tuning!` declaration in
`src/tuning/mod.rs` names each value's group, default, unit, range and
`FIRMWARE_*` environment variable:

```rust
tuning! {
    /// Control-panel buttons.
    buttons: ButtonTuning {
        /// How long a new level must hold before it counts as a press or release.
        debounce: 20 ms in 1..=500 from "FIRMWARE_BUTTON_DEBOUNCE_MS";
    }
}
```

It generates a `ButtonTuning` struct with `DEFAULT`, its field in `Tuning`, and
an entry in `Tuning::VARIABLES`. The unit picks the field type: `ms` is a
`Duration`, `scans` a `u8`. `main.rs` calls `Tuning::from_env()` before
starting anything and passes each group to its adapter. Overrides are logged;
an unknown `FIRMWARE_*` name is a warning; a value that is not a whole number or
is out of range fails startup with an error naming the variable and its range.

The image installs `yocto/meta-firmware/recipes-firmware/firmware/files/firmware.env`
as `/etc/default/firmware`, a conffile that `firmware.service` reads with
`EnvironmentFile=`. It lists every variable commented out at its default. On the
device, uncomment a line, change the value and run `systemctl restart firmware`;
`journalctl -u firmware` shows the overrides or the rejection. The file is
rendered from `Tuning::VARIABLES` (`tuning::env_file`), and a test fails with the
expected text when the shipped copy differs, so a new variable needs that file
updated too.
