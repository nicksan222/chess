//! The connection status screen: a placeholder until its integration is implemented.

use super::{Reporter, Transition};
use crate::menu::Request;

/// Finishes immediately; replace with the real integration.
pub struct ConnectionStatus;

impl Transition for ConnectionStatus {
    const REQUEST: Request = Request::ShowConnectionStatus;

    type Settings = ();
    type Status = ();

    fn new(_: &()) -> Self {
        Self
    }

    fn start(&mut self, report: Reporter<()>) {
        report.finish(());
    }
}
