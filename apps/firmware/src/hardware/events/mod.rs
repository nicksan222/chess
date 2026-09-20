//! Values reported by the physical hardware adapters.
//!
//! These events describe physical controls and piece presence without exposing
//! the GPIO, I2C, or sensing technology used to observe them. Game rules and
//! chess-piece identity belong outside the hardware layer.

mod piece;

use super::pins::ButtonEvent;

pub use piece::{BoardPosition, PieceEvent};

/// An observation emitted by an input hardware adapter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HardwareEvent {
    Button(ButtonEvent),
    Piece(PieceEvent),
}

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
