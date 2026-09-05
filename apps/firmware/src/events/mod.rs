#![allow(clippy::upper_case_acronyms)]

//! Typed hardware events and the bounded queue used to deliver them.
//!
//! Hardware interface names retain their schematic spellings (`GPIO`, `I2C`,
//! and `SPI`) throughout this API.
//!
//! Producers own a cheap-to-clone [`EventEmitter`]. Emitting asynchronously
//! waits for queue capacity, applying backpressure rather than dropping an
//! observation or growing memory without bound. Consumers own the single
//! [`EventReceiver`].

mod gpio;
mod i2c;
mod spi;

use tokio::sync::mpsc;

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

/// A cloneable handle used by hardware workers to emit events.
///
/// The emitter deliberately wraps Tokio's sender: callers can submit any typed
/// event that converts into [`Event`], while queue mechanics remain local to
/// this module.
#[derive(Clone, Debug)]
pub struct EventEmitter {
    sender: mpsc::Sender<Event>,
}

impl EventEmitter {
    /// Emits an event, waiting until the bounded queue has capacity.
    ///
    /// On failure, [`EmitError`] returns ownership of the event so the producer
    /// can log it, retry it elsewhere, or shut down cleanly.
    pub async fn emit<E>(&self, event: E) -> Result<(), EmitError>
    where
        E: Into<Event>,
    {
        self.sender.send(event.into()).await
    }

    /// Attempts to emit an event without waiting for queue capacity.
    ///
    /// [`TryEmitError`] distinguishes a full queue from a closed receiver and
    /// returns ownership of the event in either case.
    pub fn try_emit<E>(&self, event: E) -> Result<(), TryEmitError>
    where
        E: Into<Event>,
    {
        self.sender.try_send(event.into())
    }

    /// Sends an already-erased event, waiting for queue capacity.
    ///
    /// Prefer [`Self::emit`] in producers so concrete event values are
    /// converted at the boundary automatically.
    pub async fn send(&self, event: Event) -> Result<(), EmitError> {
        self.sender.send(event).await
    }

    /// Attempts to send an already-erased event without waiting.
    ///
    /// This mirrors [`mpsc::Sender::try_send`] for callers that already hold an
    /// [`Event`]. Prefer [`Self::try_emit`] for concrete event types.
    pub fn try_send(&self, event: Event) -> Result<(), TryEmitError> {
        self.sender.try_send(event)
    }

    /// Returns `true` after the event receiver has been dropped or closed.
    pub fn is_closed(&self) -> bool {
        self.sender.is_closed()
    }
}

/// Failure to emit because the event receiver has closed.
pub type EmitError = mpsc::error::SendError<Event>;

/// Failure to emit immediately because the queue is full or closed.
pub type TryEmitError = mpsc::error::TrySendError<Event>;

/// Sending half of the bounded firmware event queue.
pub type EventSender = EventEmitter;

/// Receiving half of the bounded firmware event queue.
pub type EventReceiver = mpsc::Receiver<Event>;

/// Creates the bounded queue shared by hardware producers and the coordinator.
///
/// # Panics
///
/// Panics when `capacity` is zero or exceeds Tokio's supported channel capacity.
/// A bounded queue applies backpressure instead of allowing delayed hardware
/// events to consume memory indefinitely.
pub fn channel(capacity: usize) -> (EventEmitter, EventReceiver) {
    let (sender, receiver) = mpsc::channel(capacity);
    (EventEmitter { sender }, receiver)
}
