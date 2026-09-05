//! The linked list that serves as the authoritative game timeline.

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
/// chronological [`LinkedList`]. Each
/// step commits to its event and every preceding event.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GameHistory {
    steps: LinkedList<HistoryStep>,
    anchor: HistoryHash,
    tip: HistoryHash,
}

impl GameHistory {
    /// Creates an empty history at the genesis hash.
    ///
    /// The new [`GameHistory`] retains no [`HistoryStep`] values. Its
    /// anchor and tip are both [`HistoryHash::GENESIS`], so the next
    /// accepted event receives [`Ply::FIRST`] and commits to genesis.
    /// Use [`GameHistory::for_board`] when the timeline must commit
    /// to a concrete initial [`Board`].
    #[must_use]
    pub const fn new() -> Self {
        Self {
            steps: LinkedList::new(),
            anchor: HistoryHash::GENESIS,
            tip: HistoryHash::GENESIS,
        }
    }

    /// Creates an empty history anchored to a specific initial board.
    ///
    /// The new [`GameHistory`] retains no [`HistoryStep`] values. Its
    /// anchor and tip are both the board commitment returned for
    /// `board`, so [`GameHistory::verify`] replays the hash chain
    /// from that anchor and the next event receives [`Ply::FIRST`].
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
    ///
    /// The anchor is fixed at construction: [`HistoryHash::GENESIS`]
    /// for [`GameHistory::new`], or the board commitment for
    /// [`GameHistory::for_board`]. [`GameHistory::verify`] replays
    /// every [`HistoryStep`] starting from this hash.
    #[must_use]
    pub const fn anchor(&self) -> HistoryHash {
        self.anchor
    }

    /// Returns the number of retained events.
    ///
    /// The count equals the number of [`HistoryStep`] values in the
    /// timeline. The next event therefore receives ply `len + 1`,
    /// keeping ply sequencing gapless from [`Ply::FIRST`].
    #[must_use]
    pub const fn len(&self) -> HistoryCount {
        HistoryCount::from_len(self.steps.len())
    }

    /// Returns whether no events have been recorded.
    ///
    /// An empty [`GameHistory`] has no [`HistoryStep`] values and its
    /// tip equals its anchor, so any event category may be pushed
    /// next under the active -> invalid -> final transition rules.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.steps.is_empty()
    }

    /// Returns the latest cumulative hash.
    ///
    /// The tip commits to the anchor and every retained
    /// [`HistoryStep`]. It equals the anchor while the history is
    /// empty and equals the newest step's hash otherwise. Each new
    /// step stores this value as its previous hash, forming the
    /// hash chain.
    #[must_use]
    pub const fn tip(&self) -> HistoryHash {
        self.tip
    }

    /// Returns the latest event step.
    ///
    /// The newest [`HistoryStep`] determines the transition rules for
    /// the next event and is the only candidate that
    /// [`GameHistory::resolve_latest_invalid`] may remove. Returns
    /// `None` while the timeline is empty.
    #[must_use]
    pub fn latest(&self) -> Option<HistoryStep> {
        self.steps.back().copied()
    }

    /// Returns retained steps in chronological order.
    ///
    /// The [`GameHistoryIter`] yields each [`HistoryStep`] from
    /// [`Ply::FIRST`] up to the tip. It borrows the timeline without
    /// reordering or revalidating the hash chain.
    pub fn iter(&self) -> GameHistoryIter<'_> {
        GameHistoryIter::new(self.steps.iter())
    }

    /// Creates and appends a local event step when its transition is valid.
    ///
    /// Active history accepts any event category. Once an invalid event is
    /// newest, only another invalid event may follow. Once a final event is
    /// newest, no event may follow. The returned step contains the cumulative
    /// hash suitable for transport or persistence.
    ///
    /// The new [`HistoryStep`] receives the next gapless [`Ply`] and a
    /// cumulative hash over the previous tip, its ply, and its
    /// [`HistoryEvent`]. The history tip advances to that hash, so the
    /// timeline stays anchored and newest-first resolution can later pop
    /// only the newest [`HistoryEventKind::Invalid`] entries.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError::InvalidTransition`] when the event is not
    /// permitted after the current tip: a non-invalid event after the
    /// newest event is invalid, or any event after the newest event is
    /// final.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, GameHistory, HistoryEvent, Square};
    ///
    /// let mut history = GameHistory::new();
    /// let step = history.push(HistoryEvent::Move(
    ///     ChessMove::new(Square::E2, Square::E4),
    /// ))?;
    /// assert_eq!(history.tip(), step.hash());
    /// assert_eq!(history.len().value(), 1);
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
    pub fn push(&mut self, event: HistoryEvent) -> Result<HistoryStep, HistoryError> {
        self.validate_transition(event)?;
        let ply = self.next_ply();
        let step =
            HistoryStep::from_parts(ply, event, self.tip, calculate_hash(self.tip, ply, event));
        self.append_validated(step);
        Ok(step)
    }

    /// Returns whether `incoming` is the valid next event.
    ///
    /// Checks the incoming [`HistoryStep`] against the next gapless
    /// [`Ply`], the current tip as the required previous hash, its
    /// recomputed cumulative hash, and the active -> invalid -> final
    /// transition rules. The history is not mutated, so peers can probe
    /// synchronization before calling [`GameHistory::try_append`].
    #[must_use]
    pub fn is_synced_before(&self, incoming: HistoryStep) -> bool {
        self.validate_next(incoming).is_ok()
    }

    /// Validates and appends a step received from another component.
    ///
    /// This low-level operation checks hashes and structural transitions but
    /// cannot validate chess semantics. Use [`Game::accept`](crate::Game::accept)
    /// when applying peer events to a game.
    ///
    /// The incoming [`HistoryStep`] must carry the next gapless [`Ply`],
    /// commit to the current tip as its previous hash, carry the correct
    /// cumulative hash, and satisfy the active -> invalid -> final
    /// transition rules. On success the tip advances to the appended hash.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError::Ply`] when the step skips or repeats a ply,
    /// [`HistoryError::PreviousHash`] when it does not commit to the local
    /// tip, [`HistoryError::Hash`] when its cumulative hash is wrong, and
    /// [`HistoryError::InvalidTransition`] when its event category cannot
    /// follow the newest event.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, GameHistory, HistoryEvent, Square};
    ///
    /// let mut sender = GameHistory::new();
    /// let step = sender.push(HistoryEvent::Move(
    ///     ChessMove::new(Square::E2, Square::E4),
    /// ))?;
    /// let mut receiver = GameHistory::new();
    /// receiver.try_append(step)?;
    /// assert_eq!(receiver.tip(), sender.tip());
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
    pub fn try_append(&mut self, incoming: HistoryStep) -> Result<(), HistoryError> {
        self.validate_next(incoming)?;
        self.append_validated(incoming);
        Ok(())
    }

    /// Resolves and removes the latest invalid state.
    ///
    /// Invalid states can only be resolved newest-first. Moves and final states
    /// cannot be removed through this API.
    ///
    /// The newest [`HistoryStep`] must hold a [`HistoryEventKind::Invalid`]
    /// event. Resolution pops that step and restores the tip to its previous
    /// hash, keeping the remaining hash chain anchored and contiguous.
    /// Repeated calls therefore unwind stacked invalid states newest-first.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError::NothingToResolve`] when the history is empty,
    /// or when the newest event is a move or a final state.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{GameHistory, HistoryEvent, HistoryEventKind, InvalidState};
    ///
    /// let mut history = GameHistory::new();
    /// history.push(HistoryEvent::Invalid(InvalidState::PendingInvalid))?;
    /// let resolved = history.resolve_latest_invalid()?;
    /// assert_eq!(resolved.event().kind(), HistoryEventKind::Invalid);
    /// assert!(history.is_empty());
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
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
    ///
    /// Verification starts from the retained board anchor, checks every
    /// sequence number and cumulative hash, and finally confirms the cached
    /// tip. It does not replay chess moves; [`Game::verify`](crate::Game::verify)
    /// adds board-cache and final-state verification.
    ///
    /// Each [`HistoryStep`] must carry the next gapless [`Ply`] from
    /// [`Ply::FIRST`], commit to the running hash starting at the anchor,
    /// and carry the matching cumulative hash. The running hash must equal
    /// the cached tip once every step has been replayed.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError::Ply`] for a skipped or repeated ply,
    /// [`HistoryError::PreviousHash`] for a step that does not commit to
    /// its predecessor, [`HistoryError::Hash`] for a wrong cumulative
    /// hash, and [`HistoryError::Tip`] when the cached tip differs from
    /// the recomputed tip.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, GameHistory, HistoryEvent, Square};
    ///
    /// let mut history = GameHistory::new();
    /// history.push(HistoryEvent::Move(
    ///     ChessMove::new(Square::E2, Square::E4),
    /// ))?;
    /// history.verify()?;
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
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

    /// Validates an incoming step against the next ply, tip, and transition.
    ///
    /// The candidate [`HistoryStep`] must carry the next gapless [`Ply`],
    /// commit to the current tip as its previous hash, carry the correct
    /// cumulative hash, and satisfy the active -> invalid -> final
    /// transition rules. Used by [`GameHistory::is_synced_before`] and
    /// [`GameHistory::try_append`] before the tip advances.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError::Ply`] for a skipped or repeated ply,
    /// [`HistoryError::PreviousHash`] when the step does not commit to the
    /// local tip, [`HistoryError::Hash`] for a wrong cumulative hash, and
    /// [`HistoryError::InvalidTransition`] when the event category cannot
    /// follow the newest event.
    pub(crate) fn validate_next(&self, incoming: HistoryStep) -> Result<(), HistoryError> {
        validate_step(incoming, self.next_ply(), self.tip)?;
        self.validate_transition(incoming.event())
    }

    /// Appends an already validated step and advances the tip.
    ///
    /// The caller must have checked the [`HistoryStep`] with
    /// [`GameHistory::validate_next`]. The tip advances to the appended
    /// hash so later steps commit to this event, preserving the
    /// anchor-to-tip hash chain and gapless [`Ply`] sequencing.
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
