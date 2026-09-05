use std::{error::Error as StdError, fmt};

use tokio::sync::broadcast;

use super::Event;

const EVENT_CAPACITY: usize = 64;

/// A cloneable event producer and subscription factory.
#[derive(Clone, Debug)]
pub struct EventEmitter {
    sender: broadcast::Sender<Event>,
}

impl EventEmitter {
    /// Creates an event stream with enough retained messages for brief
    /// scheduling delays between producers and consumers.
    pub fn new() -> Self {
        let (sender, _) = broadcast::channel(EVENT_CAPACITY);
        Self { sender }
    }

    /// Creates an independent subscription to subsequently emitted events.
    pub fn subscribe(&self) -> EventSubscription {
        EventSubscription {
            receiver: self.sender.subscribe(),
        }
    }

    /// Emits an event to every current subscription.
    ///
    /// Returns the event when no subscriptions exist.
    pub fn emit(&self, event: Event) -> Result<(), EmitError> {
        self.sender
            .send(event)
            .map(|_| ())
            .map_err(|error| EmitError(error.0))
    }

    /// Returns the number of current subscriptions.
    pub fn subscriber_count(&self) -> usize {
        self.sender.receiver_count()
    }
}

impl Default for EventEmitter {
    fn default() -> Self {
        Self::new()
    }
}

/// A consumer's independent position in an event stream.
#[derive(Debug)]
pub struct EventSubscription {
    receiver: broadcast::Receiver<Event>,
}

impl EventSubscription {
    /// Waits for the next domain event.
    pub async fn recv(&mut self) -> Result<Event, ReceiveError> {
        self.receiver.recv().await.map_err(ReceiveError::from)
    }

    /// Returns the next event immediately, or `Ok(None)` when none is ready.
    pub fn try_recv(&mut self) -> Result<Option<Event>, ReceiveError> {
        match self.receiver.try_recv() {
            Ok(event) => Ok(Some(event)),
            Err(broadcast::error::TryRecvError::Empty) => Ok(None),
            Err(broadcast::error::TryRecvError::Closed) => Err(ReceiveError::Closed),
            Err(broadcast::error::TryRecvError::Lagged(skipped)) => {
                Err(ReceiveError::Lagged { skipped })
            }
        }
    }
}

/// An emission rejected because the stream has no subscriptions.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EmitError(Event);

impl EmitError {
    /// Returns the event that could not be emitted.
    pub const fn into_event(self) -> Event {
        self.0
    }
}

impl fmt::Display for EmitError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("the event stream has no subscriptions")
    }
}

impl StdError for EmitError {}

/// Failure to receive from an event subscription.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReceiveError {
    /// Every emitter for the stream has been dropped.
    Closed,
    /// The subscription fell behind and skipped older events.
    Lagged { skipped: u64 },
}

impl fmt::Display for ReceiveError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Closed => formatter.write_str("the event stream is closed"),
            Self::Lagged { skipped } => {
                write!(formatter, "the subscription skipped {skipped} event(s)")
            }
        }
    }
}

impl StdError for ReceiveError {}

impl From<broadcast::error::RecvError> for ReceiveError {
    fn from(error: broadcast::error::RecvError) -> Self {
        match error {
            broadcast::error::RecvError::Closed => Self::Closed,
            broadcast::error::RecvError::Lagged(skipped) => Self::Lagged { skipped },
        }
    }
}
