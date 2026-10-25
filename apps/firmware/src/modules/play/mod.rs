//! Local and online game setup: placeholders until game setup exists.

use ::menu::{Menu, MenuItem};

/// Requests from the Play menu.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Request {
    /// Select local game setup.
    LocalGame,
    /// Select online game setup.
    OnlineGame,
}

/// Game-mode choices.
pub static MENU: Menu<'static, super::Request> = Menu::new(
    "Play",
    &[
        MenuItem::action("Local Game", super::Request::Play(Request::LocalGame)),
        MenuItem::action("Online Game", super::Request::Play(Request::OnlineGame)),
    ],
);

super::registry::placeholder! {
    /// Game setup; it offers no operations yet.
    Play
}
