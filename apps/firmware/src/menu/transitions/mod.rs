//! The integrations behind menu requests.
//!
//! Every request has a transition, defined in its own file by implementing
//! [`Transition`] and registered with one line below; see [`transition`] for
//! the contract and the kinds it supports. Requests whose integration does not
//! exist yet have placeholder transitions that finish immediately.

mod check_for_updates;
mod install_update;
mod open_network_settings;
mod scan_wifi;
mod select_local_game;
mod select_online_game;
mod show_connection_status;
mod show_session_status;
mod start_pairing;
pub mod transition;

pub use check_for_updates::{UpdateCheck, UpdateStatus};
pub(crate) use transition::report;
pub use transition::{Reporter, Transition, TransitionEvent, TransitionEventBus};

transition::transitions! {
    /// "Check for Updates": the latest GitHub release against the running version.
    update: UpdateCheck,
    install_update: install_update::UpdateInstall,
    open_network_settings: open_network_settings::NetworkSettings,
    scan_wifi: scan_wifi::WifiScan,
    select_local_game: select_local_game::LocalGameSetup,
    select_online_game: select_online_game::OnlineGameSetup,
    show_connection_status: show_connection_status::ConnectionStatus,
    show_session_status: show_session_status::SessionStatus,
    start_pairing: start_pairing::Pairing,
}
