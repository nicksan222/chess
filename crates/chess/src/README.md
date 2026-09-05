# Chess domain source

This map is for maintainers. External consumption — which types a caller holds,
which methods they invoke, and which values may leave the process — lives in
[`DESIGN.md`](../DESIGN.md). The public API is the crate root; these directories
are private.

The source tree is organized around one-way dependencies:

- `model/` contains notation-independent values and complete board state;
- `game/movement/` calculates candidates, filters king safety, and applies
  canonical board transitions;
- `game/history/` owns the authoritative linked event timeline and all stable
  SHA-256 encodings;
- `game/aggregate/` coordinates local play, peer synchronization, invalid-state
  resolution, finalization, replay, cache verification, and centralized
  lifecycle logging;
- `game/draw/` derives claims and automatic draws from the board and history;
- `game/status/` presents the lifecycle state represented by the latest event.

## State authority

The board inside `Game` is intentionally a cache. `GameHistory` is authoritative
and contains moves, invalid operations, and the final result. The history module
controls structural transitions:

- active history accepts moves, invalid states, or a final state;
- invalid history accepts only additional invalid states;
- invalid states resolve in reverse order;
- final history accepts nothing.

The aggregate controls semantic transitions. It verifies move legality before
recording a move, validates final events against the reproduced position, and
records synchronization failures as invalid events whenever history is not
already sealed.

## Embedded constraints

The crate is `no_std` and forbids unsafe code. Movement and board calculations
are allocation-free. Linked history is the deliberate allocation boundary.
Internal invariants use assertions and still depend only on the target's panic
strategy. Lifecycle diagnostics additionally use the optional global logger;
without registration, the engine stays silent.
