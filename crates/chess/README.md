# Chess domain crate

This `no_std` crate is the headless chess engine. It owns typed board values,
legal move generation, complete rule state, draw adjudication, and a
SHA-256-linked authoritative game history. It does not depend on a UI, a
logging backend, hardware, transport, or an async runtime.

[**DESIGN.md**](DESIGN.md) is the visual package map: who talks to the crate
root, which type a caller holds, and which values may leave the process.

## Authoritative history

`GameHistory` is the source of truth for state transitions. Its linked list
contains `HistoryEvent` values:

- `Move` records a canonical move accepted by the engine;
- `Invalid` records a rejected operation that requires resolution;
- `Final` records the terminal result and permanently seals the game.

Every `HistoryStep` hashes its sequence number, event payload, previous hash,
and the complete chain before it. The chain is anchored to the initial board,
so equal event streams from different starting positions cannot synchronize.
All event variants use stable, explicit encodings rather than `Debug` output or
platform-dependent representations.

Invalid events follow stack discipline. While the newest event is invalid,
moves and final events are blocked, additional invalid events may be recorded,
and resolution must proceed newest-first through
`Game::resolve_latest_invalid`. A final event accepts no successor.

The board held by `Game` is a derived cache used for efficient legal move
queries. Accepted move events can be replayed from the retained initial board,
and repetition detection deliberately derives position identity from that
history rather than keeping a second draw-state authority.

## Draw adjudication

The engine distinguishes claims from automatic results:

- threefold repetition and the fifty-move rule become typed claims;
- fivefold repetition and the seventy-five-move rule finalize automatically;
- positions with insufficient mating material finalize automatically;
- checkmate and stalemate take precedence when the last move leaves no legal
  continuation;
- claims may be evaluated against an announced move without mutating the game.

Position identity includes placement, side to move, castling rights, and an
en-passant target only when a legal en-passant capture is actually available.
Halfmove and fullmove counters do not affect repetition identity.

## Optional logging

The engine checks the logger crate's singleton at each lifecycle event. With no
registered logger, `Game::new()` and every game operation remain silent. A
hosted application can opt in once during startup:

```rust
use logger::{LevelFilter, implementations::SystemdLogger, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);
register(&LOGGER)?;
# Ok::<(), logger::RegistrationError>(())
```

Creation, accepted moves, invalid states and their resolution, synchronized
events, and terminal results all pass through one centralized logging module.
History mutation remains centralized separately, ensuring every authoritative
event follows the same logging path.

## Embedded behavior

Board values and movement rules are allocation-free. Authoritative history uses
`chess-core`'s safe linked list and therefore allocates only when retaining a
new event. Debug-only invariants use `debug_assert!` through an internal macro;
they require no logger and follow the target's configured panic strategy.
Release builds compile those checks away.

Transport and persistence layers should exchange `HistoryStep` values and
validate them through `Game::accept`. Authentication is intentionally external:
the hash chain detects corruption and divergence but does not identify a peer.
