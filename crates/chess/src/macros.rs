//! Small internal macros for crate-wide implementation conventions.

/// Implements a source-less [`core::error::Error`] for domain error values.
macro_rules! impl_error {
    ($($error:ty),+ $(,)?) => {
        $(impl core::error::Error for $error {})+
    };
}
