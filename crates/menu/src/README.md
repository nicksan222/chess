# Menu source

The source tree follows the same one-way, domain-first organization as the chess
crate:

- `model/` contains immutable menu definitions, entries, physical inputs,
  headless commands, and reusable control bindings;
- `navigation/` owns cursor state, bounded submenu history, read-only snapshots,
  emitted events, and optional external input behavior;
- `chessboard.rs` declares the product's concrete menu tree and typed actions.

`navigation` and the chessboard definition depend on `model`; model values
never depend on traversal, rendering, hardware, application state, or the chess
engine.

## Ownership boundary

Menus borrow labels, item arrays, and child menus. `MenuState` only borrows the
root tree and never owns application state. Actions stored in menu definitions
are returned by reference. Actions created by external behavior are returned by
value.

Blocking entries define separate start and escape actions. `MenuState` retains
references to both while blocked, and `MenuCallbacks` requires the application
to implement immediate, blocking-start, and blocking-abort callbacks.

`ExternalBehavior` receives application context through an immutable borrow. A
firmware adapter can therefore inspect `&Game` while retaining separate mutable
state for hardware or I/O. The crate performs no action itself: every effect is
reported to the caller as an `Event`.

## Embedded constraints

The crate is `no_std`, allocation-free, and forbids unsafe code. Navigation
history has a documented fixed bound. Rendering, GPIO access, timing, and action
execution remain adapter concerns.
