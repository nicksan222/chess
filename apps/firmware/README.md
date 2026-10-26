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

### Modules

Product behaviour lives in self-contained modules under `src/modules/`, one
folder each. A module's `mod.rs` is its facade and re-exports the module's
public surface: the facade type other code calls, `Settings` (its `Config`
field; `Default` is the network-free value tests use), `Status` (its
`Snapshot::modules` field), `Request` (its menu requests), `MENU` when it has
menu items, and the domain types its facade returns. Implementation files are
private modules; `#![deny(unreachable_pub)]` makes the compiler reject
internals that drift public. The module's `Engine` implements the `Module`
trait in `src/modules/module.rs`. It is `pub(super)` so the registry macro can
build it, which makes it visible within `src/modules/` as a whole, not just to
the registry; sibling modules use each other's facades by convention and
review, not because the compiler forbids naming an engine. The `Facade` trait
is sealed, so only the registry implements it.

The registry in `src/modules/mod.rs` lists every module once, as
`field: Facade`, for example `firmware: Updates`. The `modules!` macro declares
`pub mod field` and generates `Config` with `device()` and `offline()`,
`ModuleStatus`, the top-level
`Request` routed by type (`Request::Updates(firmware::Request::Check)`), the
dispatcher the runtime loop owns, and facade lookup. Menu requests go to the
owning module's `request`; every hardware event goes to each module's `event`,
in registry order, before the menu interprets it. `Firmware::module::<F>()` and
`FirmwareHarness::module::<F>()` return a module's facade; integration tests use
only facades, the harness, `Config`, `Request` and `Snapshot`.

Modules use each other only through facades, which are cheap clones over `Arc`,
channels or `watch`; no module lends out `&mut` state. While building, a
module asks for another's facade with `context.get::<Connection>()`. Modules are
built in registry order, so a module may only use modules listed above it;
asking for a later one fails startup with an error naming both modules, which
every harness test would report. Dependencies therefore cannot form cycles.
A facade call into another module must not hang its caller: `Updates::check`
gives the connection module one preflight probe (5 s) to answer and treats a
slower answer as unknown, and the connection module bounds reaching
NetworkManager by `connection::CONNECT_TIMEOUT` (5 s), retrying a failed or
abandoned attempt on the next operation.

To add a module:

1. Create `src/modules/<name>/mod.rs` with `Settings`, `Status`, `Request`
   (`Never` when it has no menu items), a facade type, and an `Engine`
   implementing `Module` (`new`, `facade`, and `event` and/or `request`). A
   menu-only placeholder needs only its `Request`, its `MENU` and
   `super::module::placeholder! { Facade }`, as `play` and `pairing` show.
2. Add one line `<name>: <Facade>,` to the registry, below every module it
   uses.
3. If it has menu items, define `pub static MENU` in its `mod.rs`, return it
   from `Module::MENU`, and list it in `src/menu/definition.rs`, which alone
   decides the product menu's layout. A test fails if a module with requests
   has no `MENU` or its `MENU` is not listed, and another builds the registry
   under both `Config::offline()` and `Config::device()`.

A blocking menu item holds input until its request reports `finish`; its
escape action is another request of the same module, which cancels the work.
A plain item stays free while background work reports `progress` and
`finish`; placeholders report `done` at once, leaving their status unchanged.
Reports are `ModuleEvent`s carrying the request that started the work. The
runtime loop receives them alongside hardware events, and one generic rule
releases the menu when the request blocking it finishes. Background work may
also start in `new`, reporting through the context; dropping the module stops
it. `Snapshot::blocking` names the request holding input. Tests drive the real
menu, inject reports with `FirmwareHarness::report` as they inject hardware with
`trigger`, and wait for background results with `until`.

The registered modules are:

- `connection` owns typed, presentation-agnostic Wi-Fi control. Its
  `Connection` facade reports status, scans access points, manages the WPA
  provisioning hotspot, and joins open or WPA Personal networks. Product code
  sees validated SSIDs, redacted passphrases, and domain results rather than
  command arguments or NetworkManager types. The implementation uses the
  maintained `nmrs` D-Bus client, reached lazily on the first operation; no
  shell or `nmcli` process is involved. Status comes from the Wi-Fi device's
  state, so only a radio NetworkManager confirms idle or switched off is
  `Disconnected`; a failed query is an error and an unmanaged or failed device
  is `UnknownState`. `Config::offline()` has no Wi-Fi
  control, so tests never touch D-Bus. The Yocto image includes NetworkManager
  Wi-Fi support, `wpa-supplicant`, and `dnsmasq` for NetworkManager's shared
  hotspot mode. Its menu items (Status, Scan Wi-Fi, Network Settings) and the
  captive portal are not implemented yet.
- `firmware` owns the local firmware and its updates, independent of menus and
  displays. Its facade is `Updates`, not `Firmware`, which already names the
  running instance in `runtime`; code outside the crate imports the module
  under an alias such as `firmware::{self as fw}`, since the crate is also
  `firmware`. `firmware::NAME` and `firmware::version()` name the running firmware
  and its Cargo version, used by `--version`, the startup log and the user
  agent. `Updates::check` first asks the connection module whether Wi-Fi is
  confirmed disconnected (`WifiDisconnected`), then runs preflight checks, cheapest
  first, so a failure names its cause: the system clock must be set
  (`ClockNotSet`), the release host must resolve (`Offline`) and accept a
  connection (`Unreachable`). When Wi-Fi state is unknown, as without Wi-Fi
  control, after an error or a 5 s silence, the preflight decides. It then asks the GitHub Releases API for this
  repository's latest stable release over HTTPS and compares its `v<version>`
  tag with the installed version: `NoRelease` (404), `UpToDate` or
  `Available(Release)`. A failing service is `ServiceDown`, an exhausted quota
  `RateLimited`, and other failures keep their cause chain. TLS uses `rustls` on
  `ring` with the image's `ca-certificates`, so it needs a synchronised clock.
  "Check for Updates" is blocking and presents the check as
  `Snapshot::modules.firmware`: `Checking`, then the result, `Disabled`,
  `WifiDisconnected` or `Failed`. No button is bound to escape yet, so a check
  ends with its result or a timeout: the Wi-Fi lookup and each preflight probe
  are bounded by 5 s and the release request by 15 s. Installing an update is
  not implemented.
- `play` and `pairing` hold the Play and Pairing menus' placeholders.
- `pieces` uses `chess::Square` and `chess::SquareSet` for its domain values. It has no menu items: it observes `PieceEvent`s and presents which
  squares hold a piece, and the latest observation, as `Snapshot::modules.pieces`
  and through its `Pieces` facade.

`src/menu/definition.rs` is the single product menu definition. It composes the
headless `menu` crate's primitives and each module's `MENU` into the Play,
Connection, Pairing, Update, and Settings submenus; the Settings submenu is
empty. The menu crate remains product-neutral and performs no operation.

### Hardware adapters

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

`src/hardware/hall/` polls the eight TCA9554 Hall-sensor banks on
`/dev/i2c-1`, following [host acquisition](../../docs/host.md#reading-the-board):
there is no sensor interrupt. Every 25 ms it reads banks 0x20–0x27 in order and
reports a bank's change as `PieceEvent::Placed`/`Removed` once two consecutive
scans agree. Both are starting points for prototype tuning, set on the device
by `FIRMWARE_HALL_SCAN_INTERVAL_MS` and `FIRMWARE_HALL_STABLE_SCANS` (see
Tuning). The first
stable scan reports every occupied square as placed, so consumers learn the
starting position from the same event stream. A bank that fails a read is
logged once, reports nothing (its squares are unknown, not empty), and is
reconfigured before it is trusted again; only the squares that changed while it
was unknown are reported on recovery. Failing to open the bus fails startup; an
unresponsive bank does not. `bank.rs` is a hand-maintained table of the square
on each channel, written in chess notation and checked against
`hardware/shared/hall_banks.py` by a shared contract test.
`src/hardware/linux_i2c/` implements `embedded-hal` I2C over `i2c-dev`, one
`I2C_RDWR` transfer per transaction through the safe `i2cdev` API. Blocking transfers run off the application loop, with one scan in flight.
Dropping the poller stops publication and cancels further banks; an in-flight
bank finishes before its bus is released. The poller currently owns the bus: the
display must share it through a bus-sharing handle when it is attached.

The LED worker is not implemented yet. Reusable,
function-named GPIO identities and type-safe descriptors live in
`src/hardware/pins.rs`; OS-backed implementations live alongside them (currently
`src/hardware/linux_gpio.rs`). Unused header functions are deliberately absent.
`BoardPins` describes the three interfaces in the hardware wiring contract:
I2C for the shared bus, SPI for the LED chain, and direct GPIO button lines.

## Tuning

`src/tuning/` holds values worth adjusting on a prototype without rebuilding,
currently Hall scan timing and stability, and button polling and debounce. One `tuning!` declaration in
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

The `no-hardcoded-timing` ast-grep rule (`tooling/ast-grep/rules/`) reports
literal `Duration`s and literal `sleep`/`interval`/`timeout` calls in `src/`
outside `src/tuning/`, `src/harness.rs` and test code: a value worth adjusting on
a prototype belongs in `tuning!`. A fixed protocol or network bound that is not
a prototype knob stays a named constant with a comment saying why and
`// ast-grep-ignore: no-hardcoded-timing`, as `CONNECT_TIMEOUT`,
`REQUEST_TIMEOUT` and the preflight `PROBE` do. The `pins-only-in-pins` rule
keeps BCM numbers in `src/hardware/pins.rs`. Clippy enforces the related
boundaries: only `src/tuning/` reads the environment, only `src/events/` creates
Tokio channels, and the firmware never shells out.

`tests/yocto_manifest.rs` fails when `yocto/Cargo.toml` and `Cargo.toml`
declare different dependencies or package versions.
