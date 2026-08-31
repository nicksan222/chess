# Board model crate

This crate owns integration-neutral representations of the physical board. It is
where the board's wiring becomes chess vocabulary.

It knows that a square is read by a particular pin on a particular I2C expander,
that a square is lit by a particular position in the LED chain, and how to turn a
stream of raw expander reads into settled changes. It knows nothing about how
those reads are obtained: no I2C, no SPI, no operating system. That is what lets
the mapping be tested on a host with no hardware present.

Hardware drivers, transports, and adapter concepts do not belong here.

## The mapping is a contract with the schematic

`core/names.py` under `hardware/electronics` decides which expander pin reads
which square. This crate has to make the same decision, and nothing in either
build would notice them drifting apart — so
`hardware/electronics/tests/test_host_agreement.py` checks that the two formulas
still match.

Both sides encode the same two rules:

- **Quadrant:** expander index is `(rank / 4) * 2 + (file / 4)`, and the pin
  within it is `(rank % 4) * 4 + (file % 4)`. Quadrants keep every reed trace
  short on a 320 mm board, and port A takes the lower two ranks.
- **Serpentine:** the LED chain snakes by rank from a1, so the run between
  consecutive LEDs is one square pitch everywhere.

## Debounce lives here, not on the board

The PCB deliberately carries no hardware filtering on its 64 sense lines: the
pull-ups are the expanders' own internal ones and there are no RC networks. That
saves 128 components, and moves the job here.

`Debouncer` requires a square to read the same way for a number of consecutive
samples before it believes a change, so a chattering contact never settles.
Reed contacts bounce for a millisecond or two and chess moves take hundreds, so
there is a great deal of margin to spend.
