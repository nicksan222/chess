//! Generic publication of the latest state, without queuing intermediate values.

use std::{error::Error, fmt};
use tokio::sync::watch;

/// Publishes a retained value to independent latest-state readers.
/// Intermediate updates may be coalesced; use `Bus` when every event matters.
#[derive(Debug)]
pub struct StatePublisher<T> {
    sender: watch::Sender<T>,
}

impl<T> StatePublisher<T> {
    /// Retains `initial` even before any readers subscribe.
    pub fn new(initial: T) -> Self {
        Self {
            sender: watch::Sender::new(initial),
        }
    }

    /// Creates an independent reader of the current and future state.
    pub fn subscribe(&self) -> StateSubscription<T> {
        StateSubscription {
            receiver: self.sender.subscribe(),
        }
    }

    /// Replaces the retained value, even when no readers are attached.
    pub fn replace(&self, value: T) {
        self.sender.send_replace(value);
    }

    /// Updates the retained value in place and notifies readers.
    pub fn modify(&self, update: impl FnOnce(&mut T)) {
        self.sender.send_modify(update);
    }
}

/// An independent view of retained state. No channel guards escape this API.
#[derive(Debug)]
pub struct StateSubscription<T> {
    receiver: watch::Receiver<T>,
}

impl<T> Clone for StateSubscription<T> {
    fn clone(&self) -> Self {
        Self {
            receiver: self.receiver.clone(),
        }
    }
}

impl<T: Clone> StateSubscription<T> {
    /// Returns an owned copy of the latest state.
    pub fn current(&self) -> T {
        self.receiver.borrow().clone()
    }

    /// Waits until the retained state satisfies `condition`.
    /// Checks pending state before reporting closure, so a final update is kept.
    ///
    /// # Errors
    /// Returns `StateClosed` if the publisher closes before the condition holds.
    pub async fn wait_for(&mut self, condition: impl Fn(&T) -> bool) -> Result<T, StateClosed> {
        loop {
            // Release the channel guard before invoking application code.
            let value = self.receiver.borrow_and_update().clone();
            if condition(&value) {
                return Ok(value);
            }
            self.receiver.changed().await.map_err(|_| StateClosed)?;
        }
    }
}

/// The state publisher closed before a reader's condition was satisfied.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct StateClosed;

impl fmt::Display for StateClosed {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("the state publisher is closed")
    }
}
impl Error for StateClosed {}

#[cfg(test)]
mod tests {
    use super::{StateClosed, StatePublisher};

    #[derive(Clone, Debug, Eq, PartialEq)]
    struct Counter(u32);

    #[test]
    fn values_are_retained_without_readers_and_late_readers_see_the_latest() {
        let publisher = StatePublisher::new(Counter(0));
        publisher.replace(Counter(1));
        publisher.modify(|value| value.0 += 1);
        let first = publisher.subscribe();
        let second = first.clone();
        assert_eq!(first.current(), Counter(2));
        assert_eq!(second.current(), Counter(2));
        publisher.replace(Counter(3));
        assert_eq!(first.current(), Counter(3));
        assert_eq!(second.current(), Counter(3));
    }

    #[test]
    fn predicates_can_publish_follow_up_state_without_holding_a_channel_guard() {
        let (done, result) = std::sync::mpsc::channel();
        // A separate thread keeps a lock regression from blocking the test runner.
        std::thread::spawn(move || {
            let runtime = tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .unwrap();
            let publisher = StatePublisher::new(Counter(0));
            let mut reader = publisher.subscribe();
            let state = runtime.block_on(reader.wait_for(|value| {
                if value.0 == 0 {
                    publisher.replace(Counter(1));
                }
                value.0 == 1
            }));
            done.send(state).unwrap();
        });
        assert_eq!(
            result
                .recv_timeout(std::time::Duration::from_secs(1))
                .unwrap(),
            Ok(Counter(1))
        );
    }

    #[tokio::test]
    async fn waiting_observes_the_final_pending_value_before_closure() {
        let publisher = StatePublisher::new(Counter(0));
        let mut reader = publisher.subscribe();
        publisher.replace(Counter(1));
        publisher.replace(Counter(2));
        drop(publisher);
        assert_eq!(reader.wait_for(|value| value.0 == 2).await, Ok(Counter(2)));
        assert_eq!(
            reader.wait_for(|value| value.0 == 3).await,
            Err(StateClosed)
        );
    }

    #[tokio::test]
    async fn waiting_rechecks_updates_until_the_condition_is_satisfied() {
        let publisher = StatePublisher::new(Counter(0));
        let mut reader = publisher.subscribe();
        let publish = async {
            tokio::task::yield_now().await;
            publisher.replace(Counter(1));
            tokio::task::yield_now().await;
            publisher.modify(|value| value.0 = 2);
        };
        let (result, ()) = tokio::join!(reader.wait_for(|value| value.0 == 2), publish);
        assert_eq!(result, Ok(Counter(2)));
    }
}
