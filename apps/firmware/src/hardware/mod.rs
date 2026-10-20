//! Thin adapters over the board's physical interfaces.

pub mod button_panel;
mod buttons;
mod debounce;
pub mod display;
pub mod events;
#[cfg(target_os = "linux")]
pub mod linux_gpio;
pub mod pins;

pub use events::{
    BoardPosition, HardwareEvent, HardwareEventBus, HardwareEventSubscription, PieceEvent,
};
