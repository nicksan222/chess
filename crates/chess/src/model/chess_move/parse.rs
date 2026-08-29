use core::{fmt, str::FromStr};

use crate::{ParseSquareError, PieceKind};

use super::ChessMove;

/// The reason a coordinate move such as `e2e4` could not be parsed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ParseMoveError {
    /// A move must contain an origin, destination, and optional promotion.
    Length,
    /// The origin square is malformed.
    Origin(ParseSquareError),
    /// The destination square is malformed.
    Destination(ParseSquareError),
    /// The promotion character is not `n`, `b`, `r`, or `q`.
    Promotion,
}

impl fmt::Display for ParseMoveError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Length => formatter.write_str(
                "a move must contain four characters, plus an optional promotion character",
            ),
            Self::Origin(error) => write!(formatter, "invalid origin square: {error}"),
            Self::Destination(error) => write!(formatter, "invalid destination square: {error}"),
            Self::Promotion => {
                formatter.write_str("a promotion must select a knight, bishop, rook, or queen")
            }
        }
    }
}

impl core::error::Error for ParseMoveError {
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::Origin(error) | Self::Destination(error) => Some(error),
            Self::Length | Self::Promotion => None,
        }
    }
}

impl FromStr for ChessMove {
    type Err = ParseMoveError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        if !matches!(value.len(), 4 | 5) {
            return Err(ParseMoveError::Length);
        }
        let from = value
            .get(..2)
            .ok_or(ParseMoveError::Origin(ParseSquareError::Length))?
            .parse()
            .map_err(ParseMoveError::Origin)?;
        let to = value
            .get(2..4)
            .ok_or(ParseMoveError::Destination(ParseSquareError::Length))?
            .parse()
            .map_err(ParseMoveError::Destination)?;
        let Some(promotion) = value.as_bytes().get(4) else {
            return Ok(Self::new(from, to));
        };
        let kind = match promotion.to_ascii_lowercase() {
            b'n' => PieceKind::Knight,
            b'b' => PieceKind::Bishop,
            b'r' => PieceKind::Rook,
            b'q' => PieceKind::Queen,
            _ => return Err(ParseMoveError::Promotion),
        };
        Self::promotion(from, to, kind).map_err(|_| ParseMoveError::Promotion)
    }
}
