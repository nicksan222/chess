# Firmware

## Purpose

Track firmware scope and development decisions.

## Known direction

Firmware will target the RP2350 ARM Cortex-M33 in Rust. Embassy is the intended
future runtime. The independently configured firmware application lives in
`apps/firmware`, while platform details remain isolated from shared crates.

## TODO

Set up the embedded runtime, memory layout, dependencies, and build validation.
