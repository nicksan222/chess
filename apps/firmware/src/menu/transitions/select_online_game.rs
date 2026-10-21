//! Online game setup: a placeholder until its integration is implemented.

use super::{Reporter, Transition};
use crate::menu::Request;

/// Finishes immediately; replace with the real integration.
pub struct OnlineGameSetup;

impl Transition for OnlineGameSetup {
    const REQUEST: Request = Request::SelectOnlineGame;

    type Settings = ();
    type Status = ();

    fn new(_: &()) -> Self {
        Self
    }

    fn start(&mut self, report: Reporter<()>) {
        report.finish(());
    }
}
