//! Product menu composition and externally implemented transitions.

mod definition;
pub(crate) mod transitions;

pub use definition::{
    CONNECTION_MENU, MAIN_MENU, PAIRING_MENU, PLAY_MENU, Request, SETTINGS_MENU, Screen,
    UPDATE_MENU,
};
