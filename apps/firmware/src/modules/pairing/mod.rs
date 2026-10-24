//! Pairing and online-session controls: placeholders until pairing exists.

use ::menu::{Menu, MenuItem};

/// Requests from the Pairing menu.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Request {
    /// Start the externally managed pairing flow.
    Start,
    /// Show current online-session status.
    SessionStatus,
}

/// Pairing and online-session controls.
pub static MENU: Menu<'static, super::Request> = Menu::new(
    "Pairing",
    &[
        MenuItem::action("Start Pairing", super::Request::Pairing(Request::Start)),
        MenuItem::action(
            "Session Status",
            super::Request::Pairing(Request::SessionStatus),
        ),
    ],
);

super::module::placeholder! {
    /// Pairing and online sessions; it offers no operations yet.
    Pairing
}
