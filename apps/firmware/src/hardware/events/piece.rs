use super::BoardPosition;

/// A physical piece-presence transition observed at a board position.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PieceEvent {
    Placed(BoardPosition),
    Removed(BoardPosition),
}

impl PieceEvent {
    pub const fn position(self) -> BoardPosition {
        match self {
            Self::Placed(position) | Self::Removed(position) => position,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{BoardPosition, PieceEvent};
    use crate::hardware::HardwareEvent;

    #[test]
    fn every_board_position_round_trips_through_piece_events() {
        for row in 0..BoardPosition::SIZE {
            for column in 0..BoardPosition::SIZE {
                let position = BoardPosition::new(row, column).unwrap();
                assert_eq!(position.row(), row);
                assert_eq!(position.column(), column);

                for event in [PieceEvent::Placed(position), PieceEvent::Removed(position)] {
                    assert_eq!(event.position(), position);
                    assert_eq!(HardwareEvent::from(event), HardwareEvent::Piece(event));
                }
            }
        }
    }
}
