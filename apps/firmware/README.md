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
dispatch. Requests without a transition are placeholders, logged and ignored.
A test checks every registered transition against its menu item.

The kind follows from the menu item and what the transition reports. A
blocking item holds input until the transition reports `finish`; escape calls
`cancel`. A plain item stays free while a background transition reports
`progress` and `finish`, or an immediate one finishes inside `start`. Reports
are `TransitionEvent`s, which the runtime loop receives alongside hardware
events; one generic rule releases the menu when the request blocking it
finishes. `Snapshot::blocking` names the operation holding input. Tests drive
the real menu, inject reports with `FirmwareHarness::report` as they inject
hardware with `trigger`, and wait for background results with `until`.

Check for Updates asks the GitHub Releases API for this repository's latest
stable release over HTTPS and reports `Snapshot::transitions.update`:
`Checking`, then `Available` when its `v<version>` tag is newer than the running Cargo version,
`UpToDate`, `NoRelease` (404), `Disabled` or `Failed` with the cause. It
downloads nothing. TLS uses `rustls` on `ring` with the image's
`ca-certificates`, so it needs a synchronised clock. No button is bound to
escape yet, so a check ends with its result or a 15 s timeout.

`src/hardware/buttons.rs` and `src/hardware/debounce.rs` own polling, active-low
translation, and mechanical debounce. Call `start_subscription` with a GPIO
reader, then await `on_message` for debounced pressed/released transitions.
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
