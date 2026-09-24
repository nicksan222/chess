use std::{error::Error as StdError, fmt};

use tokio::sync::mpsc;

/// Creates a bounded, exclusive point-to-point channel.
///
/// Unlike [`super::Bus`], each value has exactly one destination. The
/// sender and receiver are deliberately not cloneable, so ownership identifies
/// the single producer and consumer. Sending waits when `capacity` values are
/// already queued, providing backpressure instead of dropping work.
pub fn direct_channel<T>(capacity: usize) -> (DirectSender<T>, DirectReceiver<T>) {
    let (sender, receiver) = mpsc::channel(capacity);
    (DirectSender { sender }, DirectReceiver { receiver })
}

/// The sole producer side of a bounded point-to-point channel.
#[derive(Debug)]
pub struct DirectSender<T> {
    sender: mpsc::Sender<T>,
}

impl<T> DirectSender<T> {
    /// Sends one value, waiting for queue capacity when the consumer is behind.
    ///
    /// Returns ownership of the value if the receiver has been dropped.
    pub async fn send(&self, value: T) -> Result<(), DirectSendError<T>> {
        self.sender
            .send(value)
            .await
            .map_err(|error| DirectSendError(error.0))
    }
}

/// The sole consumer side of a bounded point-to-point channel.
#[derive(Debug)]
pub struct DirectReceiver<T> {
    receiver: mpsc::Receiver<T>,
}

impl<T> DirectReceiver<T> {
    /// Waits for the next value, or returns `None` after the sender is dropped
    /// and all queued values have been consumed.
    pub async fn recv(&mut self) -> Option<T> {
        self.receiver.recv().await
    }
}

/// A value that could not be delivered because its receiver was dropped.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DirectSendError<T>(T);

impl<T> DirectSendError<T> {
    /// Returns the value that could not be delivered.
    pub fn into_inner(self) -> T {
        self.0
    }
}

impl<T> fmt::Display for DirectSendError<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("the direct event receiver is closed")
    }
}

impl<T: fmt::Debug> StdError for DirectSendError<T> {}

#[cfg(test)]
mod tests {
    use super::direct_channel;

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum TestEvent {
        First,
        Second,
    }

    #[tokio::test]
    async fn delivers_once_and_applies_backpressure() {
        let (sender, mut receiver) = direct_channel(1);
        sender.send(TestEvent::First).await.unwrap();

        let blocked_send = tokio::spawn(async move { sender.send(TestEvent::Second).await });
        tokio::task::yield_now().await;
        assert!(!blocked_send.is_finished());

        assert_eq!(receiver.recv().await, Some(TestEvent::First));
        blocked_send.await.unwrap().unwrap();
        assert_eq!(receiver.recv().await, Some(TestEvent::Second));
    }
}
