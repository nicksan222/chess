# Menu tests

Three test targets, from smallest to broadest. Run them all with
`just --justfile crates/menu/justfile test`.

| Target       | Question it answers                                            |
| ------------ | -------------------------------------------------------------- |
| `unit`       | Does each building block behave as documented?                 |
| `e2e`        | Do realistic user and firmware journeys read and work right?   |
| `properties` | Does `MenuState` agree with a reference model on every input?  |

## `unit/`

One module per topic, each named after what it covers: `item`, `controls`,
`menu`, `cursor`, `submenus`, `blocking`, `snapshot`, `dispatch` and
`external`. Shared fixtures and the `Recorder` callback live in `common/`.

## `e2e/`

Journeys through a product-shaped menu: browsing, blocking updates completed
or cancelled, live application state overriding a button, and rendering from
snapshots.

## `properties/`

`reference.rs` restates the documented behavior as a plain stack machine.
`fixture.rs` builds a tree with every entry kind, custom controls, an empty
menu, a cycle back to the root and a self-opening menu that reaches the depth
limit. `exhaustive.rs` checks every sequence of six operations; `randomized.rs`
runs long seeded sessions through all four `handle*` entry points and fails if
any `Event` variant was never produced.

Cyclic menus make derived `PartialEq` and `Debug` on `Menu` and `MenuItem`
recurse forever, so these tests compare menus and entries by identity.
