/// Emits a record through the registered logger at an explicit level.
#[macro_export]
macro_rules! log {
    (level: $level:expr, target: $target:expr, $($argument:tt)+) => {{
        if let Some(__logger) = $crate::get() {
            let __metadata = $crate::Metadata::new($level, $target).with_source(
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

/// Defines one `#[macro_export]` macro per level. `$d` receives a literal `$`
/// so the generated macros can declare their own repetitions.
macro_rules! define_level_macros {
    ($d:tt $($(#[$doc:meta])* $name:ident => $level:ident;)+) => {
        $(
            $(#[$doc])*
            #[macro_export]
            macro_rules! $name {
                (target: $target:expr, $d($d argument:tt)+) => {
                    $crate::log!(level: $crate::Level::$level, target: $target, $d($d argument)+)
                };
                ($d($d argument:tt)+) => {
                    $crate::log!(level: $crate::Level::$level, $d($d argument)+)
                };
            }
        )+
    };
}

define_level_macros! {
    $
    /// Emits an error record through the registered logger.
    error => Error;
    /// Emits a warning record through the registered logger.
    warn => Warn;
    /// Emits an informational record through the registered logger.
    info => Info;
    /// Emits a debug record through the registered logger.
    debug => Debug;
    /// Emits a trace record through the registered logger.
    trace => Trace;
}
