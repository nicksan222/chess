use crate::pins::{GPIO, Level};

/// An electrical level observed on a GPIO line.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct GPIOLevelEvent {
    gpio: GPIO,
    level: Level,
}

impl GPIOLevelEvent {
    pub const fn new(gpio: GPIO, level: Level) -> Self {
        Self { gpio, level }
    }

    pub const fn gpio(self) -> GPIO {
        self.gpio
    }

    pub const fn level(self) -> Level {
        self.level
    }
}
