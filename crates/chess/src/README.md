# Chess domain source

The source tree is organized as cohesive domain modules with one-way
responsibilities:

- `model/` owns notation-independent values and complete board state;
- `rules/` owns chess rules: `movement/` generates and applies canonical legal
  moves, while `draw/` derives claims and automatic adjudication;
- `history/` owns the authoritative event timeline, stable SHA-256 encodings,
  sequence and hash validation, and synchronization error values;
- `game/` is the aggregate boundary. It coordinates play, synchronization,
  invalid-state recovery, finalization, status, replay, cache verification, and
  lifecycle logging;
- `player/` owns move sources and their restricted position capability: local
  human input, transport-fed online input, and the computer-search adapter;
- `session/` assigns players to colors and is the only orchestration layer that
  polls a player and commits its response through the game aggregate.

`lib.rs` keeps these modules private and re-exports the stable public API at the
crate root. The filesystem can therefore express ownership without forcing
callers to depend on internal module paths.

## Dependency direction

`model` is foundational. `rules` evaluates and transforms model values.
`history` records stable domain events and position commitments. `game`
combines those domains while retaining exclusive control of authoritative game
transitions. `player` receives a restricted read-only game view, and `session`
coordinates players through the public game API.

The important boundary is mutation: a player can inspect a position and propose
a move, but cannot mutate a board cache, append history, resolve invalid events,
or finalize a game. `GameSession` consumes that proposal through `Game::play`,
so local, computer, and online play all follow identical rule validation,
history, logging, and adjudication paths.

## State authority

The board inside `Game` is intentionally a cache. `GameHistory` is authoritative
and contains moves, invalid operations, and the final result. The history module
controls structural transitions:

- active history accepts moves, invalid states, or a final state;
- invalid history accepts only additional invalid states;
- invalid states resolve in reverse order;
- final history accepts nothing.

The game aggregate controls semantic transitions. It verifies move legality
before recording a move, validates final events against the reproduced
position, and records synchronization failures as invalid events whenever
history is not already sealed.

## Embedded constraints

The crate is `no_std` and forbids unsafe code. Movement and board calculations
are allocation-free. Linked history is the deliberate allocation boundary.
Internal invariants use assertions and still depend only on the target's panic
strategy. Lifecycle diagnostics additionally use the optional global logger;
without registration, the engine stays silent.
