use chess::Square;

/// A physical piece-presence transition observed at a board position.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PieceEvent {
    Placed(Square),
    Removed(Square),
}

impl PieceEvent {
    pub const fn position(self) -> Square {
        match self {
            Self::Placed(position) | Self::Removed(position) => position,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{PieceEvent, Square};
    use crate::hardware::HardwareEvent;

    #[test]
    fn every_board_position_round_trips_through_piece_events() {
        for position in Square::all() {
            for event in [PieceEvent::Placed(position), PieceEvent::Removed(position)] {
                assert_eq!(event.position(), position);
                assert_eq!(HardwareEvent::from(event), HardwareEvent::Piece(event));
            }
        }
    }
}
