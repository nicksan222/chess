#![allow(clippy::upper_case_acronyms)]

//! Typed hardware events and publish-subscribe delivery.
//!
//! Hardware interface names retain their schematic spellings (`GPIO`, `I2C`,
//! and `SPI`) throughout this API.
//!
//! Each producer owns a cheap-to-clone [`EventEmitter`], and each consumer owns
//! an independent [`EventSubscription`]. Every event emitted after a consumer
//! subscribes is delivered to that subscription. Slow consumers report how
//! many events they missed instead of applying global backpressure to unrelated
//! producers and consumers.

mod gpio;
mod i2c;
mod spi;

use std::{error::Error as StdError, fmt};

use tokio::sync::broadcast;

pub use gpio::GPIOLevelEvent;
pub use i2c::{I2CEvent, I2COperation};
pub use spi::SPIEvent;

/// An event produced by one of the board's three hardware interfaces.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Event {
    GPIOLevel(GPIOLevelEvent),
    I2C(I2CEvent),
    SPI(SPIEvent),
}

impl From<GPIOLevelEvent> for Event {
    fn from(event: GPIOLevelEvent) -> Self {
        Self::GPIOLevel(event)
    }
}

impl From<I2CEvent> for Event {
    fn from(event: I2CEvent) -> Self {
        Self::I2C(event)
    }
}

impl From<SPIEvent> for Event {
    fn from(event: SPIEvent) -> Self {
        Self::SPI(event)
    }
}

/// A cloneable event producer and subscription factory.
///
/// Cloning an emitter creates another producer for the same event stream.
#[derive(Clone, Debug)]
pub struct EventEmitter {
    sender: broadcast::Sender<Event>,
}

impl EventEmitter {
    /// Creates an event stream retaining up to `capacity` unread events for
    /// each subscription.
    ///
    /// # Panics
    ///
    /// Panics when `capacity` is zero or exceeds the supported channel
    /// capacity.
    pub fn new(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
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
    /// Returns the event when no subscriptions exist, allowing the producer to
    /// recover or log the value without cloning it first.
    pub fn emit<E>(&self, event: E) -> Result<(), EmitError>
    where
        E: Into<Event>,
    {
        self.sender
            .send(event.into())
            .map(|_| ())
            .map_err(|error| EmitError(error.0))
    }

    /// Returns the number of current subscriptions.
    pub fn subscriber_count(&self) -> usize {
        self.sender.receiver_count()
    }
}

/// A consumer's independent position in an event stream.
#[derive(Debug)]
pub struct EventSubscription {
    receiver: broadcast::Receiver<Event>,
}

impl EventSubscription {
    /// Waits for the next event emitted to this subscription.
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
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EmitError(Event);

impl EmitError {
    /// Returns the event that could not be emitted.
    pub fn into_event(self) -> Event {
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
