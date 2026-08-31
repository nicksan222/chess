# Protocol

## Purpose

Describe communication models shared between the bridge and its adapters.

## Scope

This is **not** a hardware protocol. The board carries no microcontroller, so
there is no wire format between the sensing hardware and the game logic: the
Raspberry Pi reads the expanders over I2C and shifts the LED frame out over SPI
directly. Turning those bytes into squares is `crates/board-model`'s job, and
that is a function call rather than a message.

What remains for this crate is the boundary between bridge core and its adapters,
which stays independent of transport and of any particular integration.

An earlier revision put a microcontroller on the board and would have needed a
register map here for the two processors to agree on. Removing the
microcontroller removed the protocol with it.

## TODO

Design messages, serialization and versioning for the adapter boundary. None are
selected in this scaffold.
