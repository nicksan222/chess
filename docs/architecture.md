# Architecture

## Purpose

Describe how the parts of the system relate, and why the boundaries fall where
they do.

## One processor

```text
        Physical Board
     64 Hall sensors, 64 LEDs, 12 buttons
              |
      I2C, SPI, GPIO  (no protocol)
              |
              v
      Raspberry Pi Zero 2 W
          chess -> bridge core
              |
              v
         Local Adapter
```

The board carries no microcontroller. A Raspberry Pi Zero 2 W reads the sensors
and drives the LEDs directly, so there is no second processor, no firmware, and
no wire protocol between the sensing hardware and the game logic.

That absence is the point. A microcontroller — even one with deliberately frozen,
fixed-function firmware — would mean a second toolchain, a cross-compilation
target, a flashing procedure and a register map that two codebases have to keep
agreeing on. Removing it removes all four. See [`hardware.md`](hardware.md) for
the two component choices that make it possible.

## Layers

- **`crates/chess`** is the game: board state, move generation, history. It has
  no idea a physical board exists. Applications consume it through the crate
  root; see [`crates/chess/DESIGN.md`](../crates/chess/DESIGN.md).
- **`crates/core`** holds small integration-neutral building blocks.
- **`crates/menu`** owns the board's headless menu definition and the reusable
  cursor and navigation model behind it. Input mapping and presentation remain
  adapters in the applications.
- **`apps/firmware`** owns everything shipped to the Pi: the Rust process,
  Yocto configuration, character devices, display, buttons, network provisioning,
  and systemd units.

Offline chess behavior is the initial focus. Integration-specific code stays in
adapter directories, so additional adapters can be introduced without changing
bridge core or the shared crates.

## Where the contracts are

- **The physical stack.** `hardware/shared/dimensions.py` decides the heights
  that let the plate sit flush over the board, and validates that they sum
  correctly on import.

## TODO

Design the bridge-to-adapter message set. None of it is selected yet.
