//! The contract every menu-request integration implements, and the registry
//! that wires implementations into the firmware.
//!
//! A transition is defined entirely in its own file by implementing
//! [`Transition`], then registered with one line in `transitions!`. Its kind
//! follows from its menu item and what it reports:
//!
//! - **Blocking:** a `MenuItem::blocking_action` whose escape action is
//!   [`Transition::CANCEL`]. The menu holds input until the transition reports
//!   [`Reporter::finish`]; escape calls [`Transition::cancel`].
//! - **Background:** a plain `MenuItem::action`. It reports progress and
//!   results while the menu stays free.
//! - **Immediate:** a plain `MenuItem::action` that reports `finish` from
//!   [`Transition::start`] itself, as the placeholders for not-yet-implemented
//!   integrations do.
//!
//! A transition without settings or status uses `()` for either.

use std::fmt::Debug;

use ::menu::MenuState;

use super::{StatusUpdate, TransitionStatus};
use crate::{events::Bus, menu::Request};

/// The integration behind one menu request.
pub trait Transition: Send + 'static {
    /// The request that starts this transition.
    const REQUEST: Request;
    /// The escape action that cancels it; only blocking transitions have one.
    const CANCEL: Option<Request> = None;

    /// What it reads from the firmware configuration. `Default` is the
    /// network-free value hardware-free tests run with.
    type Settings: Debug + Default;
    /// What it presents in the firmware snapshot.
    type Status: Clone + Debug + Default + Eq + Send + 'static;

    /// The settings of the installed product.
    fn device() -> Self::Settings {
        Self::Settings::default()
    }

    /// Builds the per-instance state. The firmware loop owns it, so stopping
    /// the loop drops it; dropping must stop any background work.
    fn new(settings: &Self::Settings) -> Self;

    /// Handles [`Transition::REQUEST`].
    fn start(&mut self, report: Reporter<Self::Status>);

    /// Handles [`Transition::CANCEL`] after escape aborted the blocking item.
    fn cancel(&mut self, report: Reporter<Self::Status>) {
        let _ = report;
    }
}

/// Implemented by `transitions!` for each registered transition.
pub trait Registered: Transition {
    #[doc(hidden)]
    fn wrap(status: Self::Status) -> StatusUpdate;
}

/// A report from the work behind a menu request, often running in the
/// background.
///
/// The lifecycle is generic: a finished report for the request blocking the
/// menu releases it, whatever the transition.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TransitionEvent {
    request: Request,
    finished: bool,
    status: StatusUpdate,
}

impl TransitionEvent {
    /// `T`'s work is still running.
    pub fn progress<T: Registered>(status: T::Status) -> Self {
        Self {
            request: T::REQUEST,
            finished: false,
            status: T::wrap(status),
        }
    }

    /// `T`'s work is done; a menu blocked on it resumes.
    pub fn finished<T: Registered>(status: T::Status) -> Self {
        Self {
            request: T::REQUEST,
            finished: true,
            status: T::wrap(status),
        }
    }
}

/// Bus carrying transition reports back to the firmware loop.
pub type TransitionEventBus = Bus<TransitionEvent>;

/// How a transition reports progress and results of its work.
#[derive(Clone)]
pub struct Reporter<S> {
    events: TransitionEventBus,
    event: fn(bool, S) -> TransitionEvent,
}

impl<S> Reporter<S> {
    pub(super) fn new<T: Registered<Status = S>>(events: &TransitionEventBus) -> Self {
        Self {
            events: events.clone(),
            event: |finished, status| {
                if finished {
                    TransitionEvent::finished::<T>(status)
                } else {
                    TransitionEvent::progress::<T>(status)
                }
            },
        }
    }

    /// The work is still running.
    pub fn progress(&self, status: S) {
        self.send((self.event)(false, status));
    }

    /// The work is done.
    pub fn finish(&self, status: S) {
        self.send((self.event)(true, status));
    }

    fn send(&self, event: TransitionEvent) {
        // Emitting fails only once the firmware loop has stopped listening.
        let _ = self.events.emit(event);
    }
}

/// Records a report and releases the menu when the request blocking it is done.
pub(crate) fn report(
    event: TransitionEvent,
    menu: &mut MenuState<'static, Request>,
    status: &mut TransitionStatus,
) {
    if event.finished && menu.blocking_action() == Some(&event.request) {
        menu.unblock();
    }
    status.apply(event.status);
}

/// Registers transitions: one line per transition, `field: Type`.
///
/// Generates `Config` and `TransitionStatus` with one field per transition,
/// the `Transitions` dispatcher the firmware loop owns, and `REGISTERED`, the
/// request pairs the menu-consistency test checks.
macro_rules! transitions {
    ($( $(#[$doc:meta])* $field:ident : $transition:ty ),* $(,)?) => {
        /// Settings of every registered transition.
        #[derive(Debug, Default)]
        pub struct Config {
            $( $(#[$doc])* pub $field: <$transition as $crate::menu::transitions::Transition>::Settings, )*
        }

        impl Config {
            /// The settings of the installed product.
            pub fn device() -> Self {
                Self {
                    $( $field: <$transition as $crate::menu::transitions::Transition>::device(), )*
                }
            }

            /// Settings that never reach the network, for hardware-free tests.
            pub fn offline() -> Self {
                Self::default()
            }
        }

        /// What every registered transition last reported.
        #[derive(Clone, Debug, Default, Eq, PartialEq)]
        pub struct TransitionStatus {
            $( $(#[$doc])* pub $field: <$transition as $crate::menu::transitions::Transition>::Status, )*
        }

        impl TransitionStatus {
            fn apply(&mut self, update: StatusUpdate) {
                match update {
                    $( StatusUpdate::$field(status) => self.$field = status, )*
                }
            }
        }

        /// One registered transition's new status.
        #[doc(hidden)]
        #[allow(non_camel_case_types)]
        #[derive(Clone, Debug, Eq, PartialEq)]
        pub enum StatusUpdate {
            $( $field(<$transition as $crate::menu::transitions::Transition>::Status), )*
        }

        $(
            impl $crate::menu::transitions::transition::Registered for $transition {
                fn wrap(status: Self::Status) -> StatusUpdate {
                    StatusUpdate::$field(status)
                }
            }
        )*

        /// Per-instance state of every registered transition.
        pub(crate) struct Transitions {
            events: $crate::menu::transitions::TransitionEventBus,
            $( $field: $transition, )*
        }

        impl Transitions {
            pub(crate) fn new(
                config: &Config,
                events: $crate::menu::transitions::TransitionEventBus,
            ) -> Self {
                Self {
                    $( $field: <$transition as $crate::menu::transitions::Transition>::new(&config.$field), )*
                    events,
                }
            }

            /// Dispatches one menu request to the transition that claims it.
            pub(crate) fn handle(&mut self, request: $crate::menu::Request) {
                use $crate::menu::transitions::{Reporter, Transition};
                $(
                    if request == <$transition as Transition>::REQUEST {
                        return self.$field.start(Reporter::new::<$transition>(&self.events));
                    }
                    if Some(request) == <$transition as Transition>::CANCEL {
                        return self.$field.cancel(Reporter::new::<$transition>(&self.events));
                    }
                )*
                // Unreachable for menu requests: a test requires a transition for each.
                logger::warn!("{request:?} has no transition");
            }
        }

        /// `(REQUEST, CANCEL)` of every registered transition.
        #[cfg(test)]
        pub(crate) const REGISTERED: &[($crate::menu::Request, Option<$crate::menu::Request>)] = &[
            $( (
                <$transition as $crate::menu::transitions::Transition>::REQUEST,
                <$transition as $crate::menu::transitions::Transition>::CANCEL,
            ), )*
        ];
    };
}

pub(super) use transitions;

#[cfg(test)]
mod tests {
    use ::menu::{Event, Input, Menu, MenuItem};

    use super::*;
    use crate::menu::{
        MAIN_MENU,
        transitions::{REGISTERED, UpdateStatus},
    };

    fn leaves() -> Vec<&'static MenuItem<'static, Request>> {
        fn walk(
            menu: &'static Menu<'static, Request>,
            found: &mut Vec<&'static MenuItem<'static, Request>>,
        ) {
            for item in menu.items() {
                match item.as_submenu() {
                    Some(submenu) => walk(submenu, found),
                    None => found.push(item),
                }
            }
        }
        let mut found = Vec::new();
        walk(&MAIN_MENU, &mut found);
        found
    }

    #[test]
    fn every_menu_request_has_a_transition() {
        for item in leaves() {
            let request = item.as_action().expect("menu leaves are actions");
            assert!(
                REGISTERED
                    .iter()
                    .any(|(registered, _)| registered == request),
                "{request:?} has no transition"
            );
        }
    }

    #[test]
    fn every_registered_transition_matches_its_menu_item() {
        let leaves = leaves();
        for (request, cancel) in REGISTERED {
            let item = leaves
                .iter()
                .find(|item| item.as_action() == Some(request))
                .unwrap_or_else(|| panic!("{request:?} has no menu item"));
            assert_eq!(item.escape_action(), cancel.as_ref(), "{request:?}");
        }
    }

    #[test]
    fn no_request_is_claimed_twice() {
        let mut claimed: Vec<Request> = REGISTERED
            .iter()
            .flat_map(|(request, cancel)| [Some(*request), *cancel])
            .flatten()
            .collect();
        let count = claimed.len();
        claimed.sort_by_key(|request| format!("{request:?}"));
        claimed.dedup();
        assert_eq!(claimed.len(), count);
    }

    #[test]
    fn only_a_finished_report_for_the_blocking_request_releases_the_menu() {
        static BLOCKING: Menu<'static, Request> = Menu::new(
            "Test",
            &[MenuItem::blocking_action(
                "Check",
                Request::CheckForUpdates,
                Request::CancelUpdateCheck,
            )],
        );
        let event = |request, finished| TransitionEvent {
            request,
            finished,
            status: StatusUpdate::update(UpdateStatus::UpToDate),
        };
        let mut menu = MenuState::new(&BLOCKING);
        let mut status = TransitionStatus::default();
        assert_eq!(
            menu.handle(Input::Ok),
            Event::BlockingStarted(&Request::CheckForUpdates)
        );

        report(
            event(Request::CheckForUpdates, false),
            &mut menu,
            &mut status,
        );
        assert!(menu.is_blocked());
        report(event(Request::InstallUpdate, true), &mut menu, &mut status);
        assert!(menu.is_blocked());
        report(
            event(Request::CheckForUpdates, true),
            &mut menu,
            &mut status,
        );
        assert!(!menu.is_blocked());
        assert_eq!(status.update, UpdateStatus::UpToDate);
    }
}
