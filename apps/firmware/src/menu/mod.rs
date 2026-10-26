//! Product menu composition; the modules own the requests behind it.

mod definition;
mod input;

pub use definition::{MAIN_MENU, SETTINGS_MENU, Screen};

pub(crate) use input::input;
