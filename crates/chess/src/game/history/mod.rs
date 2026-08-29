mod error;
mod hashing;
mod iter;
mod values;

pub use error::HistoryError;
pub use iter::MoveHistoryIter;
pub use values::{InvalidPly, MoveCount, MoveHash, MoveStep, Ply};

use chess_core::collections::LinkedList;

use crate::{Board, ChessMove};

use hashing::{calculate_board_anchor, calculate_hash, validate_step};

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
        MoveCount::from_len(self.steps.len())
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
        MoveHistoryIter::new(self.steps.iter())
    }

    /// Creates and appends the next locally produced move step.
    pub fn push(&mut self, chess_move: ChessMove) -> MoveStep {
        let ply = self.next_ply();
        let step = MoveStep::from_parts(
            ply,
            chess_move,
            self.tip,
            calculate_hash(self.tip, ply, chess_move),
        );
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
        self.tip = step.previous_hash();
        Some(step)
    }

    /// Recomputes every link and reports the first invalid step.
    pub fn verify(&self) -> Result<(), HistoryError> {
        let mut previous = self.anchor;
        let mut expected_value = Ply::FIRST.value();
        for step in &self.steps {
            let expected_ply = Ply::new(expected_value).expect("history ply is nonzero");
            validate_step(*step, expected_ply, previous)?;
            previous = step.hash();
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
        self.tip = step.hash();
        self.steps.push_back(step);
    }

    fn next_ply(&self) -> Ply {
        let value = (self.steps.len() as u64).saturating_add(1);
        Ply::new(value).expect("a move history cannot contain enough allocated nodes to overflow")
    }
}
