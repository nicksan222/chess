/// Emits a record at an explicitly supplied level.
///
/// The default target is the call site's module path. Use `target: "name"` to
/// route the record under a different target.
#[macro_export]
macro_rules! log {
    ($logger:expr, target: $target:expr, $level:expr, $($argument:tt)+) => {{
        let __logger = &$logger;
        let __metadata = $crate::Metadata::new(
            $level,
            $target,
            Some(module_path!()),
            Some(file!()),
            Some(line!()),
        );
        if $crate::Logger::enabled(__logger, &__metadata) {
            $crate::Logger::log(
                __logger,
                $crate::Record::new(__metadata, format_args!($($argument)+)),
            );
        }
    }};
    ($logger:expr, $level:expr, $($argument:tt)+) => {
        $crate::log!($logger, target: module_path!(), $level, $($argument)+)
    };
}

/// Emits an error record.
#[macro_export]
macro_rules! error {
    ($logger:expr, target: $target:expr, $($argument:tt)+) => {
        $crate::log!($logger, target: $target, $crate::Level::Error, $($argument)+)
    };
    ($logger:expr, $($argument:tt)+) => {
        $crate::log!($logger, $crate::Level::Error, $($argument)+)
    };
}

/// Emits a warning record.
#[macro_export]
macro_rules! warn {
    ($logger:expr, target: $target:expr, $($argument:tt)+) => {
        $crate::log!($logger, target: $target, $crate::Level::Warn, $($argument)+)
    };
    ($logger:expr, $($argument:tt)+) => {
        $crate::log!($logger, $crate::Level::Warn, $($argument)+)
    };
}

/// Emits an informational record.
#[macro_export]
macro_rules! info {
    ($logger:expr, target: $target:expr, $($argument:tt)+) => {
        $crate::log!($logger, target: $target, $crate::Level::Info, $($argument)+)
    };
    ($logger:expr, $($argument:tt)+) => {
        $crate::log!($logger, $crate::Level::Info, $($argument)+)
    };
}

/// Emits a debug record.
#[macro_export]
macro_rules! debug {
    ($logger:expr, target: $target:expr, $($argument:tt)+) => {
        $crate::log!($logger, target: $target, $crate::Level::Debug, $($argument)+)
    };
    ($logger:expr, $($argument:tt)+) => {
        $crate::log!($logger, $crate::Level::Debug, $($argument)+)
    };
}

/// Emits a trace record.
#[macro_export]
macro_rules! trace {
    ($logger:expr, target: $target:expr, $($argument:tt)+) => {
        $crate::log!($logger, target: $target, $crate::Level::Trace, $($argument)+)
    };
    ($logger:expr, $($argument:tt)+) => {
        $crate::log!($logger, $crate::Level::Trace, $($argument)+)
    };
}
