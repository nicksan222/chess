/// A physical position on the board's eight-by-eight sensing grid.
///
/// Row zero is the rank-1 edge and column zero is the file-A edge, matching the
/// coordinate origin in `hardware/shared/hall_banks.py`.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct BoardPosition {
    row: u8,
    column: u8,
}

impl BoardPosition {
    pub const SIZE: u8 = 8;

    /// Creates a position from zero-based row and column coordinates.
    pub const fn new(row: u8, column: u8) -> Option<Self> {
        if row < Self::SIZE && column < Self::SIZE {
            Some(Self { row, column })
        } else {
            None
        }
    }

    /// Returns the zero-based row, increasing from rank 1 toward rank 8.
    pub const fn row(self) -> u8 {
        self.row
    }

    /// Returns the zero-based column, increasing from file A toward file H.
    pub const fn column(self) -> u8 {
        self.column
    }
}

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

    #[test]
    fn positions_outside_either_grid_axis_are_rejected() {
        for coordinate in BoardPosition::SIZE..=u8::MAX {
            assert_eq!(BoardPosition::new(coordinate, 0), None);
            assert_eq!(BoardPosition::new(0, coordinate), None);
            assert_eq!(BoardPosition::new(coordinate, coordinate), None);
        }
    }
}
