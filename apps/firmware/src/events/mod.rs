#![allow(clippy::upper_case_acronyms)]

//! Domain events and publish-subscribe delivery.
//!
//! Hardware polling translates electrical state into these domain values
//! before emission. Consumers therefore react to player intent without knowing
//! GPIO identities, voltage levels, Tokio channels, or debounce rules.

mod domain;
mod pubsub;

pub use domain::{Button, Event};
pub use pubsub::{EmitError, EventEmitter, EventSubscription, ReceiveError};
