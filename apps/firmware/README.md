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
executable and E2E tests. Hardware adapters publish domain events through
`src/events/`; Tokio channels never escape that module. `src/harness.rs` starts
the same runtime without physical adapters and provides an acknowledged
`trigger` operation, so tests never race the event loop or duplicate production
behavior.

```sh
cargo test -p firmware --test e2e
```

The E2E cases live in `tests/e2e/`. Each harness owns isolated state and can be
restarted in the same process.

Button pins in `src/pins/gpio/button/` own polling, active-low translation, and
mechanical debounce. Call `start_subscription` with a GPIO reader, then await
`on_message` for domain-level pressed/released actions. Callers do not inspect
GPIO levels or raw hardware events.

The remaining hardware workers are not implemented yet. The board contract uses
polled TCA9554 input-port reads at eight addresses, not a GPIO sensor interrupt;
see [host acquisition](../../docs/host.md#reading-the-board). Reusable,
function-named GPIO identities and type-safe descriptors live in `src/pins/`;
unused header functions are deliberately absent. The module mirrors the three
interfaces in the hardware wiring contract: `pins/i2c.rs` for the shared I2C
bus, `pins/spi.rs` for the LED chain, and `pins/gpio.rs` for direct button lines.
