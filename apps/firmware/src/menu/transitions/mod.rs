//! The integrations behind menu requests.
//!
//! Each transition is defined in its own file by implementing [`Transition`]
//! and registered with one line below; see [`transition`] for the contract and
//! the kinds it supports. Requests without a registered transition are logged
//! and otherwise ignored.

mod check_for_updates;
pub mod transition;

pub use check_for_updates::{UpdateCheck, UpdateStatus};
pub(crate) use transition::report;
pub use transition::{Reporter, Transition, TransitionEvent, TransitionEventBus};

transition::transitions! {
    /// "Check for Updates": the latest GitHub release against the running version.
    update: UpdateCheck,
}
