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

use super::Request;

/// Dispatches one menu request to its dedicated transition module.
pub(crate) fn handle(request: Request) {
    match request {
        Request::SelectLocalGame => select_local_game::handle(),
        Request::SelectOnlineGame => select_online_game::handle(),
        Request::ShowConnectionStatus => show_connection_status::handle(),
        Request::ScanWifi => scan_wifi::handle(),
        Request::OpenNetworkSettings => open_network_settings::handle(),
        Request::StartPairing => start_pairing::handle(),
        Request::ShowSessionStatus => show_session_status::handle(),
        Request::CheckForUpdates => check_for_updates::handle(),
        Request::InstallUpdate => install_update::handle(),
    }
}
