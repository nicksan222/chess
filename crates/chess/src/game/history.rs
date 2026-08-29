use core::{fmt, iter::FusedIterator, num::NonZeroU64};

use chess_core::collections::{Iter as LinkedListIter, LinkedList};
use sha2::{Digest, Sha256};

use crate::{Board, ChessMove, Color, PieceKind};

const HASH_DOMAIN: &[u8] = b"chess.move-chain.sha256.v1\0";
const BOARD_DOMAIN: &[u8] = b"chess.board-anchor.sha256.v1\0";

/// A one-based halfmove index in a game's move history.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct Ply(NonZeroU64);

impl Ply {
    /// The first move in a history.
    pub const FIRST: Self = Self(NonZeroU64::MIN);

    /// Creates a validated one-based ply.
    pub const fn new(value: u64) -> Result<Self, InvalidPly> {
        match NonZeroU64::new(value) {
            Some(value) => Ok(Self(value)),
            None => Err(InvalidPly),
        }
    }

    /// Returns the primitive representation for serialization.
    #[must_use]
    pub const fn value(self) -> u64 {
        self.0.get()
    }
}

impl fmt::Display for Ply {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

/// The error returned for ply zero.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct InvalidPly;

impl fmt::Display for InvalidPly {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a ply must be at least one")
    }
}

impl core::error::Error for InvalidPly {}

/// The number of moves retained by a [`MoveHistory`].
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct MoveCount(usize);

impl MoveCount {
    /// No retained moves.
    pub const ZERO: Self = Self(0);

    /// Returns the primitive representation for collection boundaries.
    #[must_use]
    pub const fn value(self) -> usize {
        self.0
    }
}

impl fmt::Display for MoveCount {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

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
    /// Use [`MoveHistory::try_append`] to validate it before accepting it.
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

/// A chronological move list whose elements form a SHA-256 hash chain.
///
/// Each element is stored in the project's safe
/// [`LinkedList`](chess_core::collections::LinkedList). A step hashes a domain
/// tag, its previous hash, its ply, and its canonically encoded move. Games
/// additionally anchor the chain to their initial board. Matching the
/// `previous_hash` of an incoming step therefore verifies synchronization
/// through every move except that new step.
///
/// The chain provides corruption and synchronization detection, not signer
/// authentication: a malicious peer able to replace the whole history can
/// recompute hashes. Protocol authentication can sign [`MoveHash`] values.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct MoveHistory {
    steps: LinkedList<MoveStep>,
    anchor: MoveHash,
    tip: MoveHash,
}

impl MoveHistory {
    /// Creates an empty history at the genesis hash.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            steps: LinkedList::new(),
            anchor: MoveHash::GENESIS,
            tip: MoveHash::GENESIS,
        }
    }

    /// Creates an empty history anchored to a specific initial board.
    ///
    /// Anchoring prevents equal move sequences played from different board
    /// states from appearing synchronized.
    #[must_use]
    pub fn for_board(board: &Board) -> Self {
        let anchor = calculate_board_anchor(board);
        Self {
            steps: LinkedList::new(),
            anchor,
            tip: anchor,
        }
    }

    /// Returns the commitment to the initial board.
    #[must_use]
    pub const fn anchor(&self) -> MoveHash {
        self.anchor
    }

    /// Returns the number of retained moves.
    #[must_use]
    pub const fn len(&self) -> MoveCount {
        MoveCount(self.steps.len())
    }

    /// Returns whether no moves have been recorded.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.steps.is_empty()
    }

    /// Returns the latest cumulative hash, or the genesis hash when empty.
    #[must_use]
    pub const fn tip(&self) -> MoveHash {
        self.tip
    }

    /// Returns the retained steps in chronological order.
    pub fn iter(&self) -> MoveHistoryIter<'_> {
        MoveHistoryIter(self.steps.iter())
    }

    /// Creates and appends the next locally produced move step.
    pub fn push(&mut self, chess_move: ChessMove) -> MoveStep {
        let ply = self.next_ply();
        let step = MoveStep {
            ply,
            chess_move,
            previous_hash: self.tip,
            hash: calculate_hash(self.tip, ply, chess_move),
        };
        self.append_validated(step);
        step
    }

    /// Returns whether this history contains exactly the moves preceding
    /// `incoming` and whether the incoming step itself has a valid hash.
    ///
    /// This is the board synchronization check to perform before applying the
    /// latest move.
    #[must_use]
    pub fn is_synced_before(&self, incoming: MoveStep) -> bool {
        self.validate_next(incoming).is_ok()
    }

    /// Validates and appends a step received from another component.
    ///
    /// The history remains unchanged on error.
    pub fn try_append(&mut self, incoming: MoveStep) -> Result<(), HistoryError> {
        self.validate_next(incoming)?;
        self.append_validated(incoming);
        Ok(())
    }

    /// Removes and returns the latest move, restoring the preceding tip.
    pub fn pop(&mut self) -> Option<MoveStep> {
        let step = self.steps.pop_back()?;
        self.tip = step.previous_hash;
        Some(step)
    }

    /// Recomputes every link and reports the first invalid step.
    pub fn verify(&self) -> Result<(), HistoryError> {
        let mut previous = self.anchor;
        let mut expected_value = Ply::FIRST.value();
        for step in &self.steps {
            let expected_ply = Ply::new(expected_value).expect("history ply is nonzero");
            validate_step(*step, expected_ply, previous)?;
            previous = step.hash;
            expected_value = expected_value.saturating_add(1);
        }
        if previous != self.tip {
            return Err(HistoryError::Tip {
                expected: previous,
                actual: self.tip,
            });
        }
        Ok(())
    }

    pub(crate) fn validate_next(&self, incoming: MoveStep) -> Result<(), HistoryError> {
        validate_step(incoming, self.next_ply(), self.tip)
    }

    pub(crate) fn append_validated(&mut self, step: MoveStep) {
        self.tip = step.hash;
        self.steps.push_back(step);
    }

    fn next_ply(&self) -> Ply {
        let value = (self.steps.len() as u64).saturating_add(1);
        Ply::new(value).expect("a move history cannot contain enough allocated nodes to overflow")
    }
}

fn validate_step(
    step: MoveStep,
    expected_ply: Ply,
    expected_previous: MoveHash,
) -> Result<(), HistoryError> {
    if step.ply != expected_ply {
        return Err(HistoryError::Ply {
            expected: expected_ply,
            actual: step.ply,
        });
    }
    if step.previous_hash != expected_previous {
        return Err(HistoryError::PreviousHash {
            ply: step.ply,
            expected: expected_previous,
            actual: step.previous_hash,
        });
    }
    let expected_hash = calculate_hash(expected_previous, expected_ply, step.chess_move);
    if step.hash != expected_hash {
        return Err(HistoryError::Hash {
            ply: step.ply,
            expected: expected_hash,
            actual: step.hash,
        });
    }
    Ok(())
}

fn calculate_board_anchor(board: &Board) -> MoveHash {
    let mut digest = Sha256::new();
    digest.update(BOARD_DOMAIN);
    for square in crate::Square::all() {
        let code = match board.piece_at(square) {
            None => 0,
            Some(piece) => {
                let color = match piece.color() {
                    Color::White => 0,
                    Color::Black => 6,
                };
                let kind = match piece.kind() {
                    PieceKind::Pawn => 1,
                    PieceKind::Knight => 2,
                    PieceKind::Bishop => 3,
                    PieceKind::Rook => 4,
                    PieceKind::Queen => 5,
                    PieceKind::King => 6,
                };
                color + kind
            }
        };
        digest.update([code]);
    }
    digest.update([match board.side_to_move() {
        Color::White => 0,
        Color::Black => 1,
    }]);
    let rights = board.castling_rights();
    digest.update([
        rights.kingside(Color::White) as u8,
        rights.queenside(Color::White) as u8,
        rights.kingside(Color::Black) as u8,
        rights.queenside(Color::Black) as u8,
    ]);
    digest.update([board
        .en_passant_target()
        .map_or(u8::MAX, |square| square.index().value())]);
    digest.update(board.halfmove_clock().value().to_be_bytes());
    digest.update(board.fullmove_number().value().to_be_bytes());
    MoveHash::from_bytes(digest.finalize().into())
}

fn calculate_hash(previous: MoveHash, ply: Ply, chess_move: ChessMove) -> MoveHash {
    let mut digest = Sha256::new();
    digest.update(HASH_DOMAIN);
    digest.update(previous.as_bytes());
    digest.update(ply.value().to_be_bytes());
    digest.update([
        chess_move.from().index().value(),
        chess_move.to().index().value(),
        chess_move.promotion_code(),
    ]);
    MoveHash::from_bytes(digest.finalize().into())
}

/// The reason a move-history link failed validation.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HistoryError {
    /// The incoming step is not next in sequence.
    Ply {
        /// The required ply.
        expected: Ply,
        /// The received ply.
        actual: Ply,
    },
    /// The incoming step does not commit to the local history tip.
    PreviousHash {
        /// The incoming step's ply.
        ply: Ply,
        /// The local tip.
        expected: MoveHash,
        /// The received previous hash.
        actual: MoveHash,
    },
    /// The step's cumulative hash is incorrect.
    Hash {
        /// The invalid step's ply.
        ply: Ply,
        /// The recomputed hash.
        expected: MoveHash,
        /// The stored or received hash.
        actual: MoveHash,
    },
    /// The cached tip does not match the final element.
    Tip {
        /// The final element's hash.
        expected: MoveHash,
        /// The cached tip.
        actual: MoveHash,
    },
}

impl fmt::Display for HistoryError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Ply { expected, actual } => {
                write!(formatter, "expected ply {expected}, received {actual}")
            }
            Self::PreviousHash { ply, .. } => {
                write!(formatter, "move {ply} does not follow the local history")
            }
            Self::Hash { ply, .. } => write!(formatter, "move {ply} has an invalid hash"),
            Self::Tip { .. } => formatter.write_str("the cached move-history tip is invalid"),
        }
    }
}

impl core::error::Error for HistoryError {}

/// An iterator over hash-linked move steps in chronological order.
pub struct MoveHistoryIter<'a>(LinkedListIter<'a, MoveStep>);

impl<'a> Iterator for MoveHistoryIter<'a> {
    type Item = &'a MoveStep;

    fn next(&mut self) -> Option<Self::Item> {
        self.0.next()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        self.0.size_hint()
    }
}

impl ExactSizeIterator for MoveHistoryIter<'_> {}
impl FusedIterator for MoveHistoryIter<'_> {}
