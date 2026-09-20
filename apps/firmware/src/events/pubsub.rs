use std::{error::Error as StdError, fmt};

use tokio::sync::broadcast;

const DEFAULT_CAPACITY: usize = 64;

/// A typed many-producer, many-subscriber event bus.
#[derive(Clone, Debug)]
pub struct Bus<T> {
    sender: broadcast::Sender<T>,
}

impl<T: Clone> Bus<T> {
    pub fn new() -> Self {
        Self::with_capacity(DEFAULT_CAPACITY)
    }

    pub fn with_capacity(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
        Self { sender }
    }

    pub fn subscribe(&self) -> Subscription<T> {
        Subscription(self.sender.subscribe())
    }

    /// Sends to every subscriber without waiting for slow consumers.
    pub fn emit(&self, event: T) -> Result<(), EmitError<T>> {
        self.sender
            .send(event)
            .map(drop)
            .map_err(|error| EmitError(error.0))
    }

    pub fn subscriber_count(&self) -> usize {
        self.sender.receiver_count()
    }
}

impl<T: Clone> Default for Bus<T> {
    fn default() -> Self {
        Self::new()
    }
}

/// An independent cursor over a [`Bus`].
#[derive(Debug)]
pub struct Subscription<T>(broadcast::Receiver<T>);

impl<T: Clone> Subscription<T> {
    pub async fn recv(&mut self) -> Result<T, ReceiveError> {
        self.0.recv().await.map_err(Into::into)
    }

    pub fn try_recv(&mut self) -> Result<Option<T>, ReceiveError> {
        match self.0.try_recv() {
            Ok(event) => Ok(Some(event)),
            Err(broadcast::error::TryRecvError::Empty) => Ok(None),
            Err(broadcast::error::TryRecvError::Closed) => Err(ReceiveError::Closed),
            Err(broadcast::error::TryRecvError::Lagged(skipped)) => {
                Err(ReceiveError::Lagged(skipped))
            }
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EmitError<T>(T);

impl<T> EmitError<T> {
    pub fn into_event(self) -> T {
        self.0
    }
}

impl<T> fmt::Display for EmitError<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("the event bus has no subscribers")
    }
}

impl<T: fmt::Debug> StdError for EmitError<T> {}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReceiveError {
    Closed,
    Lagged(u64),
}

impl fmt::Display for ReceiveError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Closed => formatter.write_str("the event bus is closed"),
            Self::Lagged(skipped) => write!(formatter, "the subscriber skipped {skipped} event(s)"),
        }
    }
}

impl StdError for ReceiveError {}

impl From<broadcast::error::RecvError> for ReceiveError {
    fn from(error: broadcast::error::RecvError) -> Self {
        match error {
            broadcast::error::RecvError::Closed => Self::Closed,
            broadcast::error::RecvError::Lagged(skipped) => Self::Lagged(skipped),
        }
    }
}
