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
    #[cfg_attr(
        not(test),
        allow(dead_code, reason = "only the registry consistency tests read it")
    )]
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
    fn event(&mut self, event: HardwareEvent, status: &mut Self::Status) {
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
    #[allow(
        unreachable_pub,
        reason = "public in name only so the sealed facade trait cannot be implemented elsewhere"
    )]
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
    #[allow(dead_code, reason = "no module reports from startup work yet")]
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
