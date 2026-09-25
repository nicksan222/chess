//! Values reported by the physical hardware adapters.
//!
//! These events describe physical controls and piece presence without exposing
//! the GPIO, I2C, or sensing technology used to observe them. Game rules and
//! chess-piece identity belong outside the hardware layer.

mod piece;

use crate::events::{Bus, Subscription};

use super::pins::ButtonEvent;

pub use piece::{BoardPosition, PieceEvent};

/// An observation emitted by an input hardware adapter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HardwareEvent {
    Button(ButtonEvent),
    Piece(PieceEvent),
}

/// Shared bus carrying every physical input observation.
pub type HardwareEventBus = Bus<HardwareEvent>;
/// Independent subscription to physical input observations.
pub type HardwareEventSubscription = Subscription<HardwareEvent>;

impl From<ButtonEvent> for HardwareEvent {
    fn from(event: ButtonEvent) -> Self {
        Self::Button(event)
    }
}

impl From<PieceEvent> for HardwareEvent {
    fn from(event: PieceEvent) -> Self {
        Self::Piece(event)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hardware::pins::Button;

    #[test]
    fn every_button_and_transition_converts_to_a_hardware_event() {
        for button in [
            Button::Up,
            Button::Down,
            Button::Left,
            Button::Right,
            Button::Ok,
            Button::Reset,
            Button::Pass,
            Button::F1,
            Button::F2,
            Button::F3,
            Button::F4,
            Button::F5,
        ] {
            for event in [ButtonEvent::Pressed(button), ButtonEvent::Released(button)] {
                assert_eq!(HardwareEvent::from(event), HardwareEvent::Button(event));
            }
        }
    }
}
