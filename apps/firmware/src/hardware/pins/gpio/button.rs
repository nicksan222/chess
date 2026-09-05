use crate::events::{Button, EventEmitter};

use super::{GPIO, Level, ReadLevel};

mod debounce;
mod subscription;

pub use subscription::{ButtonSubscription, StartSubscriptionError};

/// A control-panel button connected directly to a GPIO input.
pub struct ButtonPin<const BCM: u8> {
    gpio: GPIO,
    button: Button,
}

impl<const BCM: u8> ButtonPin<BCM> {
    pub(super) const fn new(button: Button) -> Self {
        Self {
            gpio: GPIO::new(BCM),
            button,
        }
    }

    pub const fn gpio(&self) -> GPIO {
        self.gpio
    }

    pub const fn bcm_number(&self) -> u8 {
        BCM
    }

    pub fn read_level<R: ReadLevel>(&self, reader: &mut R) -> Result<Level, R::Error> {
        reader.read_level(self.gpio)
    }

    /// Starts polling and debouncing this button.
    pub fn start_subscription<R>(
        &self,
        reader: R,
        events: &EventEmitter,
    ) -> Result<ButtonSubscription, StartSubscriptionError>
    where
        R: ReadLevel + Send + 'static,
    {
        subscription::start(self.gpio, self.button, reader, events)
    }
}

/// A debounced action from one panel button.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ButtonAction {
    Pressed,
    Released,
}
