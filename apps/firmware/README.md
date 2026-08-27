# Firmware application

This application owns Raspberry Pi Pico 2 W firmware targeting the RP2350 ARM
Cortex-M33. Its bare-metal Rust target is
`thumbv8m.main-none-eabihf`, configured in `.cargo/config.toml`.

The firmware remains separate from the root host workspace so embedded target
configuration cannot affect host-side development. Board-specific code belongs
here; platform-neutral models and behavior belong in shared crates.
