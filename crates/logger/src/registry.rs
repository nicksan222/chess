use core::{fmt, ptr};

use spin::Once;

use crate::Logger;

/// The process-wide logger used by every logging macro.
static LOGGER: Once<&'static (dyn Logger + Sync)> = Once::new();

/// Registers the process-wide logger.
///
/// Registration is permanent because a global logger must remain valid for the
/// rest of the program. Registering the same logger again is harmless;
/// attempting to replace it returns [`RegistrationError`].
pub fn register(logger: &'static (dyn Logger + Sync)) -> Result<(), RegistrationError> {
    let registered = *LOGGER.call_once(|| logger);
    if ptr::eq(registered, logger) {
        Ok(())
    } else {
        Err(RegistrationError)
    }
}

/// Returns the registered logger, or `None` when logging is not configured.
#[must_use]
pub fn get() -> Option<&'static (dyn Logger + Sync)> {
    LOGGER.get().copied()
}

/// Flushes the registered logger, if any.
pub fn flush() {
    if let Some(logger) = get() {
        logger.flush();
    }
}

/// A different global logger was already registered.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RegistrationError;

impl fmt::Display for RegistrationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a different logger is already registered")
    }
}

impl core::error::Error for RegistrationError {}
