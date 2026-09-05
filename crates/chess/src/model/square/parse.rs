//! Parsing of algebraic square coordinates.

use core::{fmt, str::FromStr};

use super::{File, Rank, Square};

/// The reason an algebraic square such as `e4` could not be parsed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ParseSquareError {
    /// A square must contain exactly one file and one rank character.
    Length,
    /// The file character is outside `a` through `h`.
    File,
    /// The rank character is outside `1` through `8`.
    Rank,
}

impl fmt::Display for ParseSquareError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Length => "a square must contain exactly two ASCII characters",
            Self::File => "a square file must be between a and h",
            Self::Rank => "a square rank must be between 1 and 8",
        })
    }
}

impl_error!(ParseSquareError);

/// Parses algebraic coordinates (`e4`) into a [`Square`].
///
/// Accepts exactly two ASCII characters: a file `a`–`h`
/// (case-insensitive) followed by a rank `1`–`8`. All other shapes and
/// characters are rejected without consulting the board.
///
/// # Errors
///
/// Returns [`ParseSquareError::Length`] when the input is not two bytes,
/// [`ParseSquareError::File`] for a bad file character, and
/// [`ParseSquareError::Rank`] for a bad rank character.
///
/// # Example
///
/// ```
/// use chess::Square;
///
/// let square: Square = "e4".parse()?;
/// assert_eq!(square, Square::E4);
/// # Ok::<(), chess::ParseSquareError>(())
/// ```
impl FromStr for Square {
    type Err = ParseSquareError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let [file, rank] = value.as_bytes() else {
            return Err(ParseSquareError::Length);
        };
        let file = match file.to_ascii_lowercase() {
            b'a' => File::A,
            b'b' => File::B,
            b'c' => File::C,
            b'd' => File::D,
            b'e' => File::E,
            b'f' => File::F,
            b'g' => File::G,
            b'h' => File::H,
            _ => return Err(ParseSquareError::File),
        };
        let rank = match rank {
            b'1' => Rank::One,
            b'2' => Rank::Two,
            b'3' => Rank::Three,
            b'4' => Rank::Four,
            b'5' => Rank::Five,
            b'6' => Rank::Six,
            b'7' => Rank::Seven,
            b'8' => Rank::Eight,
            _ => return Err(ParseSquareError::Rank),
        };
        Ok(Self::new(file, rank))
    }
}
