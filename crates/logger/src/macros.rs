/// Emits a record through the registered logger at an explicit level.
#[macro_export]
macro_rules! log {
    (level: $level:expr, target: $target:expr, $($argument:tt)+) => {{
        if let Some(__logger) = $crate::get() {
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
        }
    }};
    (level: $level:expr, $($argument:tt)+) => {
        $crate::log!(level: $level, target: module_path!(), $($argument)+)
    };
}

/// Emits an error record through the registered logger.
#[macro_export]
macro_rules! error {
    (target: $target:expr, $($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Error, target: $target, $($argument)+)
    };
    ($($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Error, $($argument)+)
    };
}

/// Emits a warning record through the registered logger.
#[macro_export]
macro_rules! warn {
    (target: $target:expr, $($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Warn, target: $target, $($argument)+)
    };
    ($($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Warn, $($argument)+)
    };
}

/// Emits an informational record through the registered logger.
#[macro_export]
macro_rules! info {
    (target: $target:expr, $($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Info, target: $target, $($argument)+)
    };
    ($($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Info, $($argument)+)
    };
}

/// Emits a debug record through the registered logger.
#[macro_export]
macro_rules! debug {
    (target: $target:expr, $($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Debug, target: $target, $($argument)+)
    };
    ($($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Debug, $($argument)+)
    };
}

/// Emits a trace record through the registered logger.
#[macro_export]
macro_rules! trace {
    (target: $target:expr, $($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Trace, target: $target, $($argument)+)
    };
    ($($argument:tt)+) => {
        $crate::log!(level: $crate::Level::Trace, $($argument)+)
    };
}
