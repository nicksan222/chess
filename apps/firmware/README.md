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
[host acquisition](../../docs/host.md#reading-the-board). Generated GPIO markers
come from the actual KiCad board, including removal of unused GPIO4.
