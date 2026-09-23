# Menu source

The source tree has two one-way layers:

- `model/` contains immutable menu definitions, entries, semantic inputs,
  headless commands, and reusable control bindings;
- `navigation/` owns cursor state, bounded submenu history, read-only snapshots,
  emitted events, and optional external input behavior.

Both layers are product-neutral. Concrete labels, actions, submenus, control
bindings, and blocking policies are composed by applications outside this
crate.

## Ownership boundary

Menus borrow labels, item arrays, and child menus. `MenuState` only borrows the
root tree and never owns application state. Actions stored in externally
provided definitions are returned by reference. Actions created by external
behavior are returned by value.

Blocking entries receive separate start and escape actions from their external
definition. `MenuState` retains references to both while blocked, and
`MenuCallbacks` lets an application handle immediate, blocking-start, and
blocking-abort events without moving effects into this crate.

`ExternalBehavior` receives application context through an immutable borrow. A
firmware adapter can therefore inspect external state while retaining separate
mutable I/O state. The crate performs no action itself: every effect is reported
to the caller as an `Event`.

## Embedded constraints

The crate is `no_std`, allocation-free, and forbids unsafe code. Navigation
history has a documented fixed bound. Rendering, GPIO access, timing, product
screens, and action execution remain application concerns.
