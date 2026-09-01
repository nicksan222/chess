use core::fmt;

/// Severity of one log record, ordered from most to least severe.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(u8)]
pub enum Level {
    /// An operation failed and requires attention.
    Error = 1,
    /// An unexpected condition occurred, but execution can continue.
    Warn = 2,
    /// A noteworthy normal event occurred.
    Info = 3,
    /// Diagnostic information useful during development.
    Debug = 4,
    /// Fine-grained diagnostic information.
    Trace = 5,
}

impl Level {
    /// Returns the conventional uppercase name of this level.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Error => "ERROR",
            Self::Warn => "WARN",
            Self::Info => "INFO",
            Self::Debug => "DEBUG",
            Self::Trace => "TRACE",
        }
    }
}

impl fmt::Display for Level {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.as_str())
    }
}

/// Maximum verbosity accepted by a logger.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(u8)]
pub enum LevelFilter {
    /// Disables every record.
    #[default]
    Off = 0,
    /// Accepts only errors.
    Error = 1,
    /// Accepts warnings and errors.
    Warn = 2,
    /// Accepts informational records and more severe records.
    Info = 3,
    /// Accepts debug records and more severe records.
    Debug = 4,
    /// Accepts every record.
    Trace = 5,
}

impl LevelFilter {
    /// Returns whether `level` is within this filter.
    pub const fn allows(self, level: Level) -> bool {
        level as u8 <= self as u8
    }

    /// Returns the conventional uppercase name of this filter.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Off => "OFF",
            Self::Error => "ERROR",
            Self::Warn => "WARN",
            Self::Info => "INFO",
            Self::Debug => "DEBUG",
            Self::Trace => "TRACE",
        }
    }
}

impl From<Level> for LevelFilter {
    fn from(level: Level) -> Self {
        match level {
            Level::Error => Self::Error,
            Level::Warn => Self::Warn,
            Level::Info => Self::Info,
            Level::Debug => Self::Debug,
            Level::Trace => Self::Trace,
        }
    }
}

impl fmt::Display for LevelFilter {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.as_str())
    }
}
