//! Differential checks of `MenuState` against an obviously correct reference.
//!
//! `fixture` defines a menu tree that exercises every entry kind, custom and
//! cyclic menus, and the depth limit. `reference` restates the documented
//! behavior as a plain stack machine. `exhaustive` compares both for every
//! short operation sequence; `randomized` drives long seeded sequences through
//! every entry point and checks that every kind of event was actually reached.

mod exhaustive;
mod fixture;
mod randomized;
mod reference;
