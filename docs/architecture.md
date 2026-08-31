# Architecture

## Purpose

Describe how the parts of the system relate, and why the boundaries fall where
they do.

## One processor

```text
        Physical Board
     64 reeds, 64 LEDs, 12 buttons
              |
      I2C, SPI, GPIO  (no protocol)
              |
              v
      Raspberry Pi Zero 2 W
   board-model -> chess -> bridge core
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

- **`crates/board-model`** turns wiring into chess vocabulary: which expander pin
  reads which square, where each square sits in the LED chain, and how to filter
  contact bounce into settled changes. It knows nothing about I2C, SPI or Linux,
  which is what lets it be tested on a host with no hardware present.
- **`crates/chess`** is the game: board state, move generation, history. It has
  no idea a physical board exists.
- **`crates/core`** holds small integration-neutral building blocks.
- **`apps/bridge`** is the program that runs on the Pi. It owns everything
  platform-specific: the character devices, the display, the buttons, the network
  provisioning and the systemd units.
- **`crates/protocol`** describes messages between the bridge and its adapters.
  It is *not* a hardware protocol; there is no second processor to agree with.

Offline chess behavior is the initial focus. Integration-specific code stays in
adapter directories, so additional adapters can be introduced without changing
bridge core or the shared crates.

## Where the contracts are

There are only two places where two things have to agree, and both are checked:

- **The board's wiring.** `hardware/electronics/core/names.py` assigns squares to
  expander pins and buttons to Broadcom lines; `crates/board-model` has to make
  the same assignment. Nothing in either build would notice them drifting apart,
  so `hardware/electronics/tests/test_host_agreement.py` compares the formulas.
- **The physical stack.** `hardware/shared/dimensions.py` decides the heights
  that let the plate sit flush over the board, and validates that they sum
  correctly on import.

## TODO

Design the bridge-to-adapter message set. None of it is selected yet.
