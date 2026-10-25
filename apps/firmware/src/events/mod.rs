//! Small, typed channel primitives. Event enums belong to their modules.

#![allow(
    clippy::disallowed_types,
    clippy::disallowed_methods,
    reason = "events is the only module that owns Tokio channels; see README"
)]

mod direct;
mod pubsub;

pub use direct::{DirectReceiver, DirectSendError, DirectSender, direct_channel};
pub use pubsub::{Bus, EmitError, ReceiveError, Subscription};
