mod error;
mod event;
mod hashing;
mod iter;
mod sequence;
mod step;

pub use error::HistoryError;
pub use event::{FinalState, HistoryEvent, HistoryEventKind, InvalidState};
pub use iter::GameHistoryIter;
pub use sequence::{HistoryCount, InvalidPly, Ply};
pub use step::{HistoryHash, HistoryStep};

use chess_core::collections::LinkedList;

use crate::Board;

use hashing::{calculate_board_anchor, calculate_hash, validate_step};

/// The authoritative, SHA-256-linked timeline of a game.
///
/// Every accepted move, invalid state, and terminal result is retained in one
/// chronological [`LinkedList`](chess_core::collections::LinkedList). Each
/// step commits to its event and every preceding event.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GameHistory {
    steps: LinkedList<HistoryStep>,
    anchor: HistoryHash,
    tip: HistoryHash,
}

impl GameHistory {
    /// Creates an empty history at the genesis hash.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            steps: LinkedList::new(),
            anchor: HistoryHash::GENESIS,
            tip: HistoryHash::GENESIS,
        }
    }

    /// Creates an empty history anchored to a specific initial board.
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
    pub const fn anchor(&self) -> HistoryHash {
        self.anchor
    }

    /// Returns the number of retained events.
    #[must_use]
    pub const fn len(&self) -> HistoryCount {
        HistoryCount::from_len(self.steps.len())
    }

    /// Returns whether no events have been recorded.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.steps.is_empty()
    }

    /// Returns the latest cumulative hash.
    #[must_use]
    pub const fn tip(&self) -> HistoryHash {
        self.tip
    }

    /// Returns the latest event step.
    #[must_use]
    pub fn latest(&self) -> Option<HistoryStep> {
        self.steps.back().copied()
    }

    /// Returns retained steps in chronological order.
    pub fn iter(&self) -> GameHistoryIter<'_> {
        GameHistoryIter::new(self.steps.iter())
    }

    /// Creates and appends a local event step when its transition is valid.
    pub fn push(&mut self, event: HistoryEvent) -> Result<HistoryStep, HistoryError> {
        self.validate_transition(event)?;
        let ply = self.next_ply();
        let step =
            HistoryStep::from_parts(ply, event, self.tip, calculate_hash(self.tip, ply, event));
        self.append_validated(step);
        Ok(step)
    }

    /// Returns whether `incoming` is the valid next event.
    #[must_use]
    pub fn is_synced_before(&self, incoming: HistoryStep) -> bool {
        self.validate_next(incoming).is_ok()
    }

    /// Validates and appends a step received from another component.
    pub fn try_append(&mut self, incoming: HistoryStep) -> Result<(), HistoryError> {
        self.validate_next(incoming)?;
        self.append_validated(incoming);
        Ok(())
    }

    /// Resolves and removes the latest invalid state.
    ///
    /// Invalid states can only be resolved newest-first. Moves and final states
    /// cannot be removed through this API.
    pub fn resolve_latest_invalid(&mut self) -> Result<HistoryStep, HistoryError> {
        let current = self.latest().map(|step| step.event().kind());
        if current != Some(HistoryEventKind::Invalid) {
            return Err(HistoryError::NothingToResolve { current });
        }
        let step = self
            .steps
            .pop_back()
            .expect("the latest event proved that history is nonempty");
        self.tip = step.previous_hash();
        Ok(step)
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

    pub(crate) fn validate_next(&self, incoming: HistoryStep) -> Result<(), HistoryError> {
        validate_step(incoming, self.next_ply(), self.tip)?;
        self.validate_transition(incoming.event())
    }

    pub(crate) fn append_validated(&mut self, step: HistoryStep) {
        self.tip = step.hash();
        self.steps.push_back(step);
    }

    fn validate_transition(&self, incoming: HistoryEvent) -> Result<(), HistoryError> {
        let current = self.latest().map(|step| step.event().kind());
        let permitted = match current {
            None | Some(HistoryEventKind::Move) => true,
            Some(HistoryEventKind::Invalid) => incoming.kind() == HistoryEventKind::Invalid,
            Some(HistoryEventKind::Final) => false,
        };
        if permitted {
            Ok(())
        } else {
            Err(HistoryError::InvalidTransition {
                current,
                incoming: incoming.kind(),
            })
        }
    }

    fn next_ply(&self) -> Ply {
        let value = (self.steps.len() as u64).saturating_add(1);
        Ply::new(value).expect("a history cannot contain enough allocated nodes to overflow")
    }
}
