//! The registration macros: `placeholder!` for menu-only modules and
//! `modules!` for the registry. The contract they implement is in `module.rs`.

/// Defines the rest of a menu-only placeholder module around its
/// hand-written `Request` and `MENU`: no settings or status, a facade named
/// `$facade` without operations, and an `Engine` whose requests finish at
/// once. Replace it with a real engine once the integration exists.
macro_rules! placeholder {
    ($(#[$doc:meta])* $facade:ident) => {
        /// The module needs no settings yet.
        pub type Settings = ();

        /// The placeholder menu items report nothing yet.
        pub type Status = ();

        $(#[$doc])*
        #[derive(Clone, Copy, Debug)]
        pub struct $facade;

        /// The placeholder engine: every request finishes at once.
        pub(super) struct Engine;

        impl $crate::modules::module::Module for Engine {
            type Settings = Settings;
            type Status = Status;
            type Request = Request;
            type Facade = $facade;

            const MENU: Option<&'static ::menu::Menu<'static, super::Request>> = Some(&MENU);

            fn new(
                _: &Settings,
                _: &$crate::modules::module::Context<'_, Status>,
            ) -> Result<Self, $crate::modules::MissingDependency> {
                Ok(Self)
            }

            fn facade(&self) -> $facade {
                $facade
            }

            fn request(
                &mut self,
                _: Request,
                report: $crate::modules::module::Reporter<Status>,
            ) {
                report.done();
            }
        }
    };
}

pub(super) use placeholder;

/// Registers modules: one line per module, `field: Facade`, in dependency
/// order. `field` is the module's folder; `Facade` names its facade type and
/// its [`Request`] variant.
///
/// Declares each `pub mod field` and generates `Config` and `ModuleStatus`
/// with one field per module, the top-level `Request`, the facade lookup,
/// `Modules`, the dispatcher the firmware loop owns, and, for tests,
/// `REGISTERED`.
macro_rules! modules {
    ($( $(#[$doc:meta])* $field:ident : $facade:ident ),* $(,)?) => {
        $( pub mod $field; )*


        /// Settings of every registered module.
        #[derive(Debug, Default)]
        pub struct Config {
            $( $(#[$doc])* pub $field: $field::Settings, )*
        }

        impl Config {
            /// The settings of the installed product.
            pub fn device() -> Self {
                Self {
                    $( $field: <$field::Engine as $crate::modules::module::Module>::device(), )*
                }
            }

            /// Settings that never reach the network, for hardware-free tests.
            pub fn offline() -> Self {
                Self::default()
            }
        }

        /// What every registered module last reported.
        #[derive(Clone, Debug, Default, Eq, PartialEq)]
        pub struct ModuleStatus {
            $( $(#[$doc])* pub $field: $field::Status, )*
        }

        impl ModuleStatus {
            fn apply(&mut self, update: StatusUpdate) {
                match update.0 {
                    $( StatusChange::$field(status) => self.$field = status, )*
                }
            }
        }

        /// One registered module's new status. Only the registry builds one.
        #[doc(hidden)]
        #[derive(Clone, Debug, Eq, PartialEq)]
        pub struct StatusUpdate(StatusChange);

        #[allow(
            non_camel_case_types,
            reason = "variants are named after the lowercase module fields"
        )]
        #[derive(Clone, Debug, Eq, PartialEq)]
        enum StatusChange {
            $( $field($field::Status), )*
        }

        /// A menu request, routed to the module that owns it.
        #[derive(Clone, Copy, Debug, Eq, PartialEq)]
        pub enum Request {
            $( $(#[$doc])* $facade($field::Request), )*
        }

        impl Request {
            /// The registry name of the module that owns this request.
            pub const fn module(self) -> &'static str {
                match self {
                    $( Self::$facade(_) => stringify!($field), )*
                }
            }
        }

        /// The facade of every built module; its fields are private.
        #[doc(hidden)]
        #[derive(Clone, Debug, Default)]
        pub struct Facades {
            $( $field: Option<$field::$facade>, )*
        }

        $(
            impl $crate::modules::module::Facade for $field::$facade {
                const MODULE: &'static str = stringify!($field);
            }

            impl $crate::modules::module::sealed::Registered for $field::$facade {
                type Status = $field::Status;

                fn find(facades: &Facades) -> Option<Self> {
                    facades.$field.clone()
                }

                fn wrap(status: Self::Status) -> StatusUpdate {
                    StatusUpdate(StatusChange::$field(status))
                }
            }
        )*

        /// Every registered module, in registry order.
        #[cfg(test)]
        const REGISTERED: &[$crate::modules::module::Registration] = &[
            $( $crate::modules::module::Registration {
                name: stringify!($field),
                menu: <$field::Engine as $crate::modules::module::Module>::MENU,
                has_requests: || {
                    ::std::any::TypeId::of::<$field::Request>()
                        != ::std::any::TypeId::of::<$crate::modules::Never>()
                },
                built: |facades| {
                    <$field::$facade as $crate::modules::module::sealed::Registered>::find(facades)
                        .is_some()
                },
            }, )*
        ];

        /// Every registered module's engine.
        pub(crate) struct Modules {
            events: $crate::modules::module::ModuleEventBus,
            $( $field: $field::Engine, )*
        }

        impl Modules {
            /// Builds every module in registry order, returning their facades.
            pub(crate) fn new(
                config: &Config,
                events: &$crate::modules::module::ModuleEventBus,
            ) -> Result<(Self, Facades), $crate::modules::module::MissingDependency> {
                use $crate::modules::module::{Context, Module, Reporter, sealed::Registered};
                let mut facades = Facades::default();
                $(
                    let $field = {
                        let reporter =
                            Reporter::new(events, None, <$field::$facade as Registered>::wrap);
                        let context = Context::new(stringify!($field), &facades, reporter);
                        <$field::Engine as Module>::new(&config.$field, &context)?
                    };
                    facades.$field = Some($field.facade());
                )*
                Ok((Self { events: events.clone(), $( $field, )* }, facades))
            }

            /// Dispatches one menu request to the module that owns it.
            pub(crate) fn request(&mut self, request: Request) {
                use $crate::modules::module::{Module, Reporter, sealed::Registered};
                match request {
                    $(
                        Request::$facade(inner) => {
                            let report = Reporter::new(
                                &self.events,
                                Some(request),
                                <$field::$facade as Registered>::wrap,
                            );
                            self.$field.request(inner, report);
                        }
                    )*
                }
            }

            /// Shows a hardware event to every module, in registry order.
            pub(crate) fn event(
                &mut self,
                event: $crate::hardware::HardwareEvent,
                status: &mut ModuleStatus,
            ) {
                use $crate::modules::module::Module;
                $( self.$field.event(event, &mut status.$field); )*
            }
        }
    };
}

pub(super) use modules;
