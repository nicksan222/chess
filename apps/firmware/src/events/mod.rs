//! Small, typed channel primitives. Event enums belong to their modules.

mod direct;
mod pubsub;

pub use direct::{DirectReceiver, DirectSendError, DirectSender, direct_channel};
pub use pubsub::{Bus, EmitError, ReceiveError, Subscription};
