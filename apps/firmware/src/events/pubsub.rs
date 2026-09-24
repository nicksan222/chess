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

#[cfg(test)]
mod tests {
    use super::{Bus, ReceiveError};

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum TestEvent {
        SensorReading(u8),
        Stopped,
    }

    #[test]
    fn callers_can_define_their_own_typed_events() {
        let bus = Bus::<TestEvent>::with_capacity(4);
        let mut subscription = bus.subscribe();

        bus.emit(TestEvent::SensorReading(42)).unwrap();
        bus.emit(TestEvent::Stopped).unwrap();

        assert_eq!(
            subscription.try_recv(),
            Ok(Some(TestEvent::SensorReading(42)))
        );
        assert_eq!(subscription.try_recv(), Ok(Some(TestEvent::Stopped)));
    }

    #[test]
    fn every_subscription_receives_events_from_every_emitter_in_order() {
        let emitter = Bus::new();
        let other_emitter = emitter.clone();
        let mut first = emitter.subscribe();
        let mut second = emitter.subscribe();

        emitter.emit(TestEvent::SensorReading(1)).unwrap();
        other_emitter.emit(TestEvent::Stopped).unwrap();

        for subscription in [&mut first, &mut second] {
            assert_eq!(
                subscription.try_recv(),
                Ok(Some(TestEvent::SensorReading(1)))
            );
            assert_eq!(subscription.try_recv(), Ok(Some(TestEvent::Stopped)));
            assert_eq!(subscription.try_recv(), Ok(None));
        }
    }

    #[test]
    fn subscriptions_report_lag_without_exposing_channel_errors() {
        let emitter = Bus::new();
        let mut subscription = emitter.subscribe();

        for _ in 0..65 {
            emitter.emit(TestEvent::Stopped).unwrap();
        }

        assert_eq!(subscription.try_recv(), Err(ReceiveError::Lagged(1)));
    }

    #[test]
    fn failed_emission_returns_ownership_of_the_event() {
        let emitter = Bus::new();
        let returned = emitter.emit(TestEvent::Stopped).unwrap_err().into_event();
        assert_eq!(returned, TestEvent::Stopped);
        assert_eq!(emitter.subscriber_count(), 0);
    }
}
