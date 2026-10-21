//! Wi-Fi scanning: a placeholder until its integration is implemented.

use super::{Reporter, Transition};
use crate::menu::Request;

/// Finishes immediately; replace with the real integration.
pub struct WifiScan;

impl Transition for WifiScan {
    const REQUEST: Request = Request::ScanWifi;

    type Settings = ();
    type Status = ();

    fn new(_: &()) -> Self {
        Self
    }

    fn start(&mut self, report: Reporter<()>) {
        report.finish(());
    }
}
