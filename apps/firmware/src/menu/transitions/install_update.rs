//! Update installation: a placeholder until its integration is implemented.

use super::{Reporter, Transition};
use crate::menu::Request;

/// Finishes immediately; replace with the real integration.
pub struct UpdateInstall;

impl Transition for UpdateInstall {
    const REQUEST: Request = Request::InstallUpdate;

    type Settings = ();
    type Status = ();

    fn new(_: &()) -> Self {
        Self
    }

    fn start(&mut self, report: Reporter<()>) {
        report.finish(());
    }
}
