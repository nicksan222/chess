//! Small internal macros for crate-wide implementation conventions.

/// Implements a source-less [`core::error::Error`] for domain error values.
macro_rules! impl_error {
    ($($error:ty),+ $(,)?) => {
        $(impl core::error::Error for $error {})+
    };
}

/// Checks an internal invariant in debug builds without requiring a logger.
///
/// On embedded targets a failed check follows the target's normal panic
/// strategy. Release builds compile the check away entirely.
macro_rules! debug_invariant {
    ($($argument:tt)*) => {
        debug_assert!($($argument)*);
    };
}
