use std::fmt;

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

    /// Parses a square name such as `"E4"`; file letters are uppercase.
    pub const fn parse(name: &str) -> Option<Self> {
        match name.as_bytes() {
            [file @ b'A'..=b'H', rank @ b'1'..=b'8'] => Self::new(*rank - b'1', *file - b'A'),
            _ => None,
        }
    }
}

impl fmt::Display for BoardPosition {
    /// Writes the square name, such as `E4`.
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{}{}",
            char::from(b'A' + self.column),
            self.row + 1
        )
    }
}

/// The [`BoardPosition`] of a square written in chess notation, such as
/// `square!(E4)`. An invalid name fails to compile.
macro_rules! square {
    ($name:ident) => {
        const {
            match $crate::hardware::BoardPosition::parse(stringify!($name)) {
                Some(position) => position,
                None => {
                    #[allow(
                        clippy::panic,
                        reason = "invalid square literals must fail at compile time"
                    )]
                    {
                        panic!(concat!("not a board square: ", stringify!($name)))
                    }
                }
            }
        }
    };
}
pub(crate) use square;

#[cfg(test)]
mod tests {
    use super::BoardPosition;

    #[test]
    fn square_names_round_trip_through_positions() {
        for row in 0..BoardPosition::SIZE {
            for column in 0..BoardPosition::SIZE {
                let position = BoardPosition::new(row, column).unwrap();
                assert_eq!(BoardPosition::parse(&position.to_string()), Some(position));
            }
        }
        assert_eq!(square!(E4), BoardPosition::new(3, 4).unwrap());
        for invalid in ["", "E", "E0", "E9", "I1", "e4", "E10"] {
            assert_eq!(BoardPosition::parse(invalid), None, "{invalid:?}");
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
