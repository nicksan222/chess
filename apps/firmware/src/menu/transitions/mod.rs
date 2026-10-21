//! Dispatch points for externally implemented menu requests.

mod check_for_updates;
mod install_update;
mod open_network_settings;
mod scan_wifi;
mod select_local_game;
mod select_online_game;
mod show_connection_status;
mod show_session_status;
mod start_pairing;

use ::menu::MenuState;

use super::Request;
use crate::events::Bus;

pub use check_for_updates::UpdateStatus;

/// Settings for the integrations behind menu requests.
///
/// The device and hardware-free tests differ only in these values, not in code
/// paths. Each integration adds its setting here.
#[derive(Debug)]
pub struct Config {
    /// Release endpoint for "Check for Updates", or `None` to disable checks.
    pub release_feed: Option<String>,
}

impl Config {
    /// The settings of the installed product.
    pub fn device() -> Self {
        Self {
            release_feed: Some(check_for_updates::GITHUB_RELEASES.to_owned()),
        }
    }

    /// Settings that never reach the network, for hardware-free tests.
    pub fn offline() -> Self {
        Self { release_feed: None }
    }
}

/// What the integrations behind menu requests last reported. Each integration
/// adds its field here.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct TransitionStatus {
    /// Latest result of "Check for Updates".
    pub update: UpdateStatus,
}

impl TransitionStatus {
    fn apply(&mut self, status: StatusUpdate) {
        match status {
            StatusUpdate::Update(update) => self.update = update,
        }
    }
}

/// One integration's new status. Each integration adds one variant.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum StatusUpdate {
    Update(UpdateStatus),
}

impl From<UpdateStatus> for StatusUpdate {
    fn from(status: UpdateStatus) -> Self {
        Self::Update(status)
    }
}

/// A report from the work behind a menu request, often running in the
/// background.
///
/// The lifecycle is generic: a finished report for the request that blocks the
/// menu releases it, whatever the integration. The status is per integration.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TransitionEvent {
    request: Request,
    finished: bool,
    status: StatusUpdate,
}

impl TransitionEvent {
    /// The work behind `request` is still running.
    pub fn progress(request: Request, status: impl Into<StatusUpdate>) -> Self {
        Self {
            request,
            finished: false,
            status: status.into(),
        }
    }

    /// The work behind `request` is done; a blocked menu waiting on it resumes.
    pub fn finished(request: Request, status: impl Into<StatusUpdate>) -> Self {
        Self {
            request,
            finished: true,
            status: status.into(),
        }
    }
}

/// Bus carrying transition reports back to the firmware loop.
pub type TransitionEventBus = Bus<TransitionEvent>;

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

/// Reports progress and results of the work behind one request.
#[derive(Clone)]
struct Reporter {
    request: Request,
    events: TransitionEventBus,
}

impl Reporter {
    fn new(request: Request, events: &TransitionEventBus) -> Self {
        Self {
            request,
            events: events.clone(),
        }
    }

    fn progress(&self, status: impl Into<StatusUpdate>) {
        self.send(TransitionEvent::progress(self.request, status));
    }

    fn finish(&self, status: impl Into<StatusUpdate>) {
        self.send(TransitionEvent::finished(self.request, status));
    }

    fn send(&self, event: TransitionEvent) {
        // Emitting fails only once the firmware loop has stopped listening.
        let _ = self.events.emit(event);
    }
}

/// State the transitions of one firmware instance keep between requests.
///
/// An integration that needs configuration, a client or background work adds
/// its field here, built from [`Config`], and reports through a [`Reporter`].
/// The firmware loop owns this, so stopping the loop drops it and cancels any
/// background work.
pub(crate) struct Transitions {
    events: TransitionEventBus,
    updates: check_for_updates::Updates,
}

impl Transitions {
    pub(crate) fn new(config: &Config, events: TransitionEventBus) -> Self {
        Self {
            events,
            updates: check_for_updates::Updates::new(config.release_feed.clone()),
        }
    }

    /// Dispatches one menu request to its dedicated transition module.
    pub(crate) fn handle(&mut self, request: Request) {
        match request {
            Request::SelectLocalGame => select_local_game::handle(),
            Request::SelectOnlineGame => select_online_game::handle(),
            Request::ShowConnectionStatus => show_connection_status::handle(),
            Request::ScanWifi => scan_wifi::handle(),
            Request::OpenNetworkSettings => open_network_settings::handle(),
            Request::StartPairing => start_pairing::handle(),
            Request::ShowSessionStatus => show_session_status::handle(),
            Request::CheckForUpdates => {
                check_for_updates::handle(&mut self.updates, Reporter::new(request, &self.events));
            }
            Request::CancelUpdateCheck => check_for_updates::cancel(
                &mut self.updates,
                Reporter::new(Request::CheckForUpdates, &self.events),
            ),
            Request::InstallUpdate => install_update::handle(),
        }
    }
}
