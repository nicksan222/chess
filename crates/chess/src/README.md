# Chess domain source

The source tree is organized by responsibility:

- `model/` contains strongly typed board values, self-locating pieces, moves,
  and complete boards;
- `game/` contains the game aggregate, legal movement rules, forced board
  relocation, and hash-linked history; each piece kind has its own movement
  calculator.

Application integration, hardware, and transport concerns do not belong here.
