use super::{GPIO, InputOutput, Pin};

/// Pins for the board's shared I2C bus.
pub struct I2cPins {
    pub data: Pin<2, InputOutput>,
    pub clock: Pin<3, InputOutput>,
}

impl I2cPins {
    pub(super) const fn get() -> Self {
        Self {
            data: Pin::new(GPIO::new(2)),
            clock: Pin::new(GPIO::new(3)),
        }
    }
}
