//! The contract every firmware module implements, and the registry that wires
//! modules into the firmware.
//!
//! A module is a folder under `modules/` whose `mod.rs` is its facade and
//! re-exports its public surface. It names, by convention, its facade type
//! (also the [`Request`] variant and registry entry), `Settings`, `Status`,
//! `Request` and, when it has menu items, `MENU`. Its `Engine` implements
//! [`Module`]; it is `pub(super)` so the registry can build it, which makes it
//! visible throughout `modules`, and siblings use facades instead by
//! convention. One line in `modules!` wires it in.
//!
//! - **Menu requests** reach the owning module's [`Module::request`]. A
//!   blocking menu item holds input until that request's [`Reporter::finish`];
//!   its escape action is another request of the same module, which cancels.
//!   An immediate request reports `finish` at once, or `done` to leave its
//!   status unchanged, as placeholders do.
//! - **Hardware events** reach every module's [`Module::event`], in registry
//!   order, before the menu interprets them.
//! - **Dependencies** are other modules' facades, looked up with
//!   [`Context::get`] while building. Modules are built in registry order, so a
//!   module may only use modules listed above it; asking for a later one fails
//!   startup with [`MissingDependency`]. Facades are cheap clones and never
//!   lend out `&mut` state.
//!
//! A module without menu items uses [`Never`] as its `Request`; one without
//! settings or status uses `()` for either.

use std::{error::Error as StdError, fmt, fmt::Debug};

use ::menu::{Menu, MenuState};

use super::{Facades, ModuleStatus, Request, StatusUpdate};
use crate::{events::Bus, hardware::HardwareEvent};

/// The engine behind one module. The firmware loop owns it, so stopping the
/// loop drops it; dropping must stop any background work it started.
pub(crate) trait Module: Sized + Send + 'static {
    /// What it reads from the firmware configuration. `Default` is the
    /// network-free value hardware-free tests run with.
    type Settings: Debug + Default;
    /// What it presents in the firmware snapshot.
    type Status: Clone + Debug + Default + Eq + Send + 'static;
    /// The menu requests it owns; [`Never`] when it has no menu items.
    type Request: Copy + Debug + Eq;
    /// The public API other modules, the executable and tests use.
    type Facade: Facade<Status = Self::Status>;

    /// Its submenu, which `menu/definition.rs` must list; `None` without menu
    /// items. Only the registry consistency tests read it.
    #[cfg_attr(not(test), allow(dead_code))]
    const MENU: Option<&'static Menu<'static, Request>> = None;

    /// The settings of the installed product.
    fn device() -> Self::Settings {
        Self::Settings::default()
    }

    /// Builds the module from its settings and the facades of the modules
    /// registered before it. Background work may start here, reporting
    /// through [`Context::reporter`].
    fn new(
        settings: &Self::Settings,
        context: &Context<'_, Self::Status>,
    ) -> Result<Self, MissingDependency>;

    /// A handle to this module's public API.
    fn facade(&self) -> Self::Facade;

    /// Observes a hardware event; `status` is this module's snapshot entry.
    fn event(&mut self, event: &HardwareEvent, status: &mut Self::Status) {
        let _ = (event, status);
    }

    /// Handles one of its menu requests.
    fn request(&mut self, request: Self::Request, report: Reporter<Self::Status>) {
        let _ = (request, report);
    }
}

/// A module's public API, looked up by type. `modules!` implements it for the
/// facade of every registered module, so each module has its own facade type.
/// It is sealed: no code outside the registry can implement it.
pub trait Facade: sealed::Registered + Clone + Send + Sync + 'static {
    /// The module's registry name.
    const MODULE: &'static str;
}

pub(super) mod sealed {
    use super::super::{Facades, StatusUpdate};

    /// What the registry needs from a facade. Public in name only, inside a
    /// private module, so nothing outside the registry can implement
    /// [`Facade`](super::Facade). `StatusUpdate` and `Facades` must then be
    /// public too, but their contents are private.
    #[allow(unreachable_pub)]
    pub trait Registered: Sized {
        /// The module's snapshot status.
        type Status;

        #[doc(hidden)]
        fn find(facades: &Facades) -> Option<Self>;

        #[doc(hidden)]
        fn wrap(status: Self::Status) -> StatusUpdate;
    }
}

/// The request type of a module without menu items; it has no values.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Never {}

/// What a module can use while it is being built.
pub(crate) struct Context<'a, S> {
    module: &'static str,
    facades: &'a Facades,
    reporter: Reporter<S>,
}

impl<'a, S: Clone> Context<'a, S> {
    pub(super) fn new(module: &'static str, facades: &'a Facades, reporter: Reporter<S>) -> Self {
        Self {
            module,
            facades,
            reporter,
        }
    }

    /// The facade of a module registered before this one.
    pub(crate) fn get<F: Facade>(&self) -> Result<F, MissingDependency> {
        F::find(self.facades).ok_or(MissingDependency {
            module: self.module,
            dependency: F::MODULE,
        })
    }

    /// Reports this module's status from work started outside any request,
    /// such as background work started while building.
    #[allow(dead_code)] // No module reports from startup work yet.
    pub(crate) fn reporter(&self) -> Reporter<S> {
        self.reporter.clone()
    }
}

/// A module asked for a module that is not built yet: it is registered after
/// the module that uses it. `Debug` prints the same sentence as `Display`, so
/// an unwrapped startup error reads well.
#[derive(Clone, Copy, Eq, PartialEq)]
pub struct MissingDependency {
    module: &'static str,
    dependency: &'static str,
}

impl fmt::Display for MissingDependency {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let Self { module, dependency } = self;
        write!(
            formatter,
            "module `{module}` uses `{dependency}`, which is not built yet; \
             register `{dependency}` before `{module}` in `modules!`"
        )
    }
}

impl Debug for MissingDependency {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(self, formatter)
    }
}

impl StdError for MissingDependency {}

/// A report from a module's work, often running in the background.
///
/// The lifecycle is generic: a finished report for the request blocking the
/// menu releases it, whatever the module.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ModuleEvent {
    pub(super) request: Option<Request>,
    pub(super) phase: Phase,
    /// `None` leaves the module's snapshot status as it was.
    pub(super) status: Option<StatusUpdate>,
}

/// Whether a report leaves the work running or ends it.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Phase {
    /// The work is still running.
    Progress,
    /// The work is done; a menu blocked on its request resumes.
    Finished,
}

impl ModuleEvent {
    /// A report of `F`'s module in `phase`, for the work `request` started or,
    /// with `None`, for work no request started.
    pub fn new<F: Facade>(request: Option<Request>, phase: Phase, status: F::Status) -> Self {
        Self {
            request,
            phase,
            status: Some(F::wrap(status)),
        }
    }
}

/// Bus carrying module reports back to the firmware loop.
pub type ModuleEventBus = Bus<ModuleEvent>;

/// How a module reports progress and results of its work.
pub(crate) struct Reporter<S> {
    events: ModuleEventBus,
    request: Option<Request>,
    wrap: fn(S) -> StatusUpdate,
}

// Derived `Clone` would needlessly require `S: Clone`.
impl<S> Clone for Reporter<S> {
    fn clone(&self) -> Self {
        Self {
            events: self.events.clone(),
            request: self.request,
            wrap: self.wrap,
        }
    }
}

impl<S> Reporter<S> {
    pub(super) fn new(
        events: &ModuleEventBus,
        request: Option<Request>,
        wrap: fn(S) -> StatusUpdate,
    ) -> Self {
        Self {
            events: events.clone(),
            request,
            wrap,
        }
    }

    /// The work is still running.
    pub(crate) fn progress(&self, status: S) {
        self.send(Phase::Progress, status);
    }

    /// The work is done.
    pub(crate) fn finish(&self, status: S) {
        self.send(Phase::Finished, status);
    }

    /// The work is done and leaves the status as it was, as placeholders do.
    pub(crate) fn done(&self) {
        self.emit(Phase::Finished, None);
    }

    fn send(&self, phase: Phase, status: S) {
        self.emit(phase, Some((self.wrap)(status)));
    }

    fn emit(&self, phase: Phase, status: Option<StatusUpdate>) {
        let event = ModuleEvent {
            request: self.request,
            phase,
            status,
        };
        // Emitting fails only once the firmware loop has stopped listening.
        let _ = self.events.emit(event);
    }
}

/// Records a report and releases the menu when the request blocking it is done.
pub(crate) fn report(
    event: ModuleEvent,
    menu: &mut MenuState<'static, Request>,
    status: &mut ModuleStatus,
) {
    if event.phase == Phase::Finished
        && event
            .request
            .is_some_and(|request| menu.blocking_action() == Some(&request))
    {
        menu.unblock();
    }
    if let Some(update) = event.status {
        status.apply(update);
    }
}

/// One registered module, as the registry consistency tests see it.
#[cfg(test)]
pub(super) struct Registration {
    pub(super) name: &'static str,
    pub(super) menu: Option<&'static Menu<'static, Request>>,
    /// Whether its `Request` has values, unlike [`Never`].
    pub(super) has_requests: fn() -> bool,
    /// Whether `Facades` holds its facade.
    pub(super) built: fn(&Facades) -> bool,
}

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

        #[allow(non_camel_case_types)]
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
        #[derive(Clone, Default)]
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
                event: &$crate::hardware::HardwareEvent,
                status: &mut ModuleStatus,
            ) {
                use $crate::modules::module::Module;
                $( self.$field.event(event, &mut status.$field); )*
            }
        }
    };
}

pub(super) use modules;
