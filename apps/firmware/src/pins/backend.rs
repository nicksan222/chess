use super::Gpio;

/// Electrical level driven on a GPIO line.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum Level {
    Low,
    High,
}

/// Hardware operation needed by writable pins.
///
/// The Linux GPIO implementation can implement this trait without leaking its
/// handle type into the board map.
pub trait OutputBackend {
    type Error;

    fn set_level(&mut self, gpio: Gpio, level: Level) -> Result<(), Self::Error>;
}
