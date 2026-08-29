use core::fmt;

use crate::ChessMove;

use super::Ply;

/// A SHA-256 commitment to a move and every move preceding it.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct MoveHash([u8; Self::BYTE_COUNT]);

impl MoveHash {
    /// The number of bytes in a move hash.
    pub const BYTE_COUNT: usize = 32;

    /// The anchor for a history that is not tied to an initial board.
    pub const GENESIS: Self = Self([0; Self::BYTE_COUNT]);

    /// Creates a hash from its transport representation.
    #[must_use]
    pub const fn from_bytes(bytes: [u8; Self::BYTE_COUNT]) -> Self {
        Self(bytes)
    }

    /// Returns the transport representation.
    #[must_use]
    pub const fn to_bytes(self) -> [u8; Self::BYTE_COUNT] {
        self.0
    }

    /// Borrows the transport representation.
    #[must_use]
    pub const fn as_bytes(&self) -> &[u8; Self::BYTE_COUNT] {
        &self.0
    }
}

impl Default for MoveHash {
    fn default() -> Self {
        Self::GENESIS
    }
}

impl fmt::Display for MoveHash {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        for byte in self.0 {
            write!(formatter, "{byte:02x}")?;
        }
        Ok(())
    }
}

impl fmt::Debug for MoveHash {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "MoveHash({self})")
    }
}

/// One immutable element in a hash-linked move history.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct MoveStep {
    ply: Ply,
    chess_move: ChessMove,
    previous_hash: MoveHash,
    hash: MoveHash,
}

impl MoveStep {
    /// Reconstructs a step received from transport or persistence.
    ///
    /// Use [`crate::MoveHistory::try_append`] to validate it before accepting it.
    #[must_use]
    pub const fn from_parts(
        ply: Ply,
        chess_move: ChessMove,
        previous_hash: MoveHash,
        hash: MoveHash,
    ) -> Self {
        Self {
            ply,
            chess_move,
            previous_hash,
            hash,
        }
    }

    /// Returns this step's one-based sequence index.
    #[must_use]
    pub const fn ply(self) -> Ply {
        self.ply
    }

    /// Returns the recorded chess move.
    #[must_use]
    pub const fn chess_move(self) -> ChessMove {
        self.chess_move
    }

    /// Returns the commitment that must match before this move is applied.
    #[must_use]
    pub const fn previous_hash(self) -> MoveHash {
        self.previous_hash
    }

    /// Returns the commitment to this move and all preceding moves.
    #[must_use]
    pub const fn hash(self) -> MoveHash {
        self.hash
    }
}
