//! Computer move source and public player construction.

use embedded_chess_engine::Evaluate;

use crate::Player;

use super::{
    super::{PlayerKind, PlayerResponse, PlayerView},
    ComputerError, Difficulty, adapter,
};

/// Internal state for a local computer player.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(in crate::player) struct Computer {
    difficulty: Difficulty,
}

impl Computer {
    /// Creates a computer source at `difficulty`.
    ///
    /// The difficulty only tunes the synchronous search depth used by
    /// [`Computer::poll`](Self::poll); it never blocks waiting for input.
    const fn new(difficulty: Difficulty) -> Self {
        Self { difficulty }
    }

    /// Searches the restricted [`PlayerView`] synchronously for a move.
    ///
    /// This poll never blocks waiting for input: the engine search runs to
    /// completion on the calling thread, consulting only the capabilities
    /// exposed by [`PlayerView`] (piece placement, legal moves, castling
    /// rights, en-passant target). It cannot mutate the [`Game`](crate::Game)
    /// or append history.
    ///
    /// A terminal position with no legal moves yields
    /// [`PlayerResponse::Pending`](super::super::PlayerResponse::Pending) so
    /// [`crate::GameSession`] can surface the terminal
    /// status on its next poll.
    ///
    /// # Errors
    ///
    /// Returns [`ComputerError`] when the position cannot be translated for
    /// search ([`InconsistentEnPassant`](ComputerError::InconsistentEnPassant),
    /// [`InvalidSquare`](ComputerError::InvalidSquare)), the engine suggests
    /// a move outside [`PlayerView::legal_moves`]
    /// ([`IllegalMove`](ComputerError::IllegalMove)), or the engine resigns
    /// while legal moves remain ([`Resigned`](ComputerError::Resigned)).
    pub(in crate::player) fn poll(
        &mut self,
        view: PlayerView<'_>,
    ) -> Result<PlayerResponse, ComputerError> {
        let board = adapter::to_search_board(view)?;
        let (selected, _, _) = board.get_best_next_move(self.difficulty.search_depth());
        let selected = adapter::from_search_move(selected, view)?;

        let Some(candidate) = selected else {
            // The engine reports resign when it sees no move. If the domain
            // agrees, yield `Pending` and let the session surface the terminal
            // status on its next poll; otherwise the divergence is an error
            // rather than a silent substitution.
            if view.legal_moves().next().is_none() {
                return Ok(PlayerResponse::Pending);
            }
            return Err(ComputerError::Resigned);
        };

        if view.legal_moves().any(|legal| legal == candidate) {
            return Ok(PlayerResponse::Move(candidate));
        }
        if view.legal_moves().next().is_none() {
            // Terminal race: the position ended between the session status
            // check and this poll. Do not invent an error for it.
            return Ok(PlayerResponse::Pending);
        }
        Err(ComputerError::IllegalMove(candidate))
    }
}

impl Player {
    /// Creates a local computer player at `difficulty`.
    ///
    /// Computer polling performs its search synchronously. Callers with a
    /// latency-sensitive loop should invoke [`crate::GameSession::poll`] from
    /// an appropriate worker context.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Difficulty, Player};
    ///
    /// let player = Player::computer(Difficulty::Medium);
    /// assert_eq!(player.difficulty(), Some(Difficulty::Medium));
    /// ```
    #[must_use]
    pub const fn computer(difficulty: Difficulty) -> Self {
        Self::from_kind(PlayerKind::Computer(Computer::new(difficulty)))
    }

    /// Returns this computer player's difficulty, or `None` for other players.
    ///
    /// Human and online [`Player`]s produce moves through the non-blocking
    /// mailbox discipline instead of a synchronous search, so they carry no
    /// [`Difficulty`] and report `None` here.
    #[must_use]
    pub const fn difficulty(&self) -> Option<Difficulty> {
        match self.kind {
            PlayerKind::Computer(computer) => Some(computer.difficulty),
            PlayerKind::Human(_) | PlayerKind::Online(_) => None,
        }
    }
}
