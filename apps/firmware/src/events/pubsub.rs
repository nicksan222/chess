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

    #[tokio::test]
    async fn recv_reports_lag_then_resumes_with_the_oldest_retained_event() {
        let bus = Bus::<u32>::with_capacity(2);
        let mut subscription = bus.subscribe();
        for value in 0..5 {
            bus.emit(value).unwrap();
        }

        assert_eq!(subscription.recv().await, Err(ReceiveError::Lagged(3)));
        assert_eq!(subscription.recv().await, Ok(3));
        assert_eq!(subscription.recv().await, Ok(4));
    }

    #[tokio::test]
    async fn closing_the_bus_drains_queued_events_then_reports_closed() {
        let bus = Bus::new();
        let mut subscription = bus.subscribe();
        bus.emit(TestEvent::Stopped).unwrap();
        drop(bus);

        assert_eq!(subscription.recv().await, Ok(TestEvent::Stopped));
        assert_eq!(subscription.recv().await, Err(ReceiveError::Closed));
        assert_eq!(subscription.try_recv(), Err(ReceiveError::Closed));
    }

    #[test]
    fn subscriber_count_tracks_subscriptions_and_clones_share_the_bus() {
        let bus = Bus::<u8>::default();
        let clone = bus.clone();
        assert_eq!(bus.subscriber_count(), 0);
        let first = bus.subscribe();
        let second = clone.subscribe();
        assert_eq!(bus.subscriber_count(), 2);
        assert_eq!(clone.subscriber_count(), 2);
        drop(first);
        assert_eq!(bus.subscriber_count(), 1);
        drop(second);
        assert_eq!(bus.subscriber_count(), 0);
    }

    #[test]
    fn a_new_subscription_does_not_see_earlier_events() {
        let bus = Bus::new();
        let mut early = bus.subscribe();
        bus.emit(TestEvent::SensorReading(1)).unwrap();
        let mut late = bus.subscribe();
        bus.emit(TestEvent::SensorReading(2)).unwrap();

        assert_eq!(early.try_recv(), Ok(Some(TestEvent::SensorReading(1))));
        assert_eq!(late.try_recv(), Ok(Some(TestEvent::SensorReading(2))));
        assert_eq!(late.try_recv(), Ok(None));
    }

    #[test]
    fn errors_have_readable_messages() {
        let emitter = Bus::new();
        let error = emitter.emit(TestEvent::Stopped).unwrap_err();
        assert_eq!(error.to_string(), "the event bus has no subscribers");
        assert_eq!(ReceiveError::Closed.to_string(), "the event bus is closed");
        assert_eq!(
            ReceiveError::Lagged(7).to_string(),
            "the subscriber skipped 7 event(s)"
        );
    }

    #[test]
    fn failed_emission_returns_ownership_of_the_event() {
        let emitter = Bus::new();
        let returned = emitter.emit(TestEvent::Stopped).unwrap_err().into_event();
        assert_eq!(returned, TestEvent::Stopped);
        assert_eq!(emitter.subscriber_count(), 0);
    }
}
