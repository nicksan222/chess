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

Hardware workers are not implemented yet. The board contract uses polled
TCA9554 input-port reads at eight addresses, not a GPIO sensor interrupt; see
[host acquisition](../../docs/host.md#reading-the-board). Reusable, function-named
GPIO identities and type-safe descriptors live in `src/pins/`; unused GPIO4 is
deliberately absent. `pins/mod.rs` owns the `Gpio` board map and `BoardPins`,
while `pins/pin.rs` defines the generic `Pin<const BCM: u8, Capability>` type.
