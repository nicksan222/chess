use super::{Output, Pin};

/// Pins for the SPI LED chain.
pub struct SPIPins {
    pub data: Pin<10, Output>,
    pub clock: Pin<11, Output>,
}

impl SPIPins {
    pub(super) const fn get() -> Self {
        Self {
            data: Pin::new(),
            clock: Pin::new(),
        }
    }
}
