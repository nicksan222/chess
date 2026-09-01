use crate::{Metadata, Record};

/// Platform-supplied destination for log records.
///
/// Implementations choose filtering, formatting, synchronization, buffering,
/// and I/O. Methods use shared references so callers can pass a logger through
/// read-only application context; stateful backends can use their platform's
/// interior-mutability or synchronization primitive.
pub trait Logger {
    /// Returns whether a record with `metadata` should be constructed.
    ///
    /// The default accepts every record. Rejecting metadata prevents the log
    /// macro's message arguments from being evaluated.
    fn enabled(&self, _metadata: &Metadata<'_>) -> bool {
        true
    }

    /// Handles one enabled record.
    fn log(&self, record: Record<'_>);

    /// Flushes any buffered records.
    fn flush(&self) {}
}

impl<L> Logger for &L
where
    L: Logger + ?Sized,
{
    fn enabled(&self, metadata: &Metadata<'_>) -> bool {
        (**self).enabled(metadata)
    }

    fn log(&self, record: Record<'_>) {
        (**self).log(record);
    }

    fn flush(&self) {
        (**self).flush();
    }
}

impl<L> Logger for &mut L
where
    L: Logger + ?Sized,
{
    fn enabled(&self, metadata: &Metadata<'_>) -> bool {
        (**self).enabled(metadata)
    }

    fn log(&self, record: Record<'_>) {
        (**self).log(record);
    }

    fn flush(&self) {
        (**self).flush();
    }
}

/// A logger which silently discards every record.
#[derive(Clone, Copy, Debug, Default)]
pub struct NopLogger;

impl Logger for NopLogger {
    fn enabled(&self, _metadata: &Metadata<'_>) -> bool {
        false
    }

    fn log(&self, _record: Record<'_>) {}
}
