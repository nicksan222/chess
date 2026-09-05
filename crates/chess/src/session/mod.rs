//! Turn ownership and player polling.

mod error;
mod update;

use crate::{
    ChessMove, Color, DrawClaim, DrawClaimError, Game, GameStatus, HistoryError, HistoryStep,
    Player,
};

use crate::player::{PlayerResponse, PlayerView};

pub use error::SessionError;
pub use update::SessionUpdate;

/// A game paired with the players that own White and Black.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GameSession {
    game: Game,
    white: Player,
    black: Player,
}

impl GameSession {
    /// Creates a standard game owned by `white` and `black`.
    ///
    /// The players are polled non-blockingly: human and online owners
    /// answer pending until a move is submitted, while computer owners
    /// search synchronously on the polling thread.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{GameSession, Player};
    ///
    /// let session = GameSession::new(Player::human(), Player::human());
    /// assert_eq!(session.game(), &chess::Game::new());
    /// ```
    #[must_use]
    pub fn new(white: Player, black: Player) -> Self {
        Self::from_game(Game::new(), white, black)
    }

    /// Attaches players to an existing game.
    ///
    /// Keeps the given position and history while assigning turn ownership;
    /// later polls still consult only the side to move and recover from
    /// rejections via [`resolve_latest_invalid`](Self::resolve_latest_invalid).
    #[must_use]
    pub const fn from_game(game: Game, white: Player, black: Player) -> Self {
        Self { game, white, black }
    }

    /// Returns the authoritative game as a read-only view.
    ///
    /// The game remains the single source of truth: players only see its
    /// restricted snapshot while polling, and consumed moves are committed
    /// through authoritative play.
    #[must_use]
    pub const fn game(&self) -> &Game {
        &self.game
    }

    /// Returns the White player.
    ///
    /// Use [`white_mut`](Self::white_mut) to submit or cancel White's
    /// staged move before its non-blocking poll.
    #[must_use]
    pub const fn white(&self) -> &Player {
        &self.white
    }

    /// Returns mutable access to the White player, not the game.
    ///
    /// Authoritative position state stays behind [`game`](Self::game); this
    /// accessor only stages input in White's single-pending mailbox slot.
    pub const fn white_mut(&mut self) -> &mut Player {
        &mut self.white
    }

    /// Returns the Black player.
    ///
    /// Use [`black_mut`](Self::black_mut) to submit or cancel Black's
    /// staged move before its non-blocking poll.
    #[must_use]
    pub const fn black(&self) -> &Player {
        &self.black
    }

    /// Returns mutable access to the Black player, not the game.
    ///
    /// Authoritative position state stays behind [`game`](Self::game); this
    /// accessor only stages input in Black's single-pending mailbox slot.
    pub const fn black_mut(&mut self) -> &mut Player {
        &mut self.black
    }

    /// Ends the session and returns its game and players.
    ///
    /// Useful when the caller takes over history inspection, persistence,
    /// or recovery directly instead of polling the session further.
    #[must_use]
    pub fn into_parts(self) -> (Game, Player, Player) {
        (self.game, self.white, self.black)
    }

    /// Returns the current lifecycle status without polling any player.
    ///
    /// Never consults a mailbox or starts a synchronous computer search;
    /// terminal and [`Invalid`](GameStatus::Invalid) states make
    /// [`poll`](Self::poll) report [`Unavailable`](SessionUpdate::Unavailable)
    /// until resolved.
    #[must_use]
    pub fn status(&self) -> GameStatus {
        self.game.status()
    }

    /// Resolves the newest invalid state newest-first.
    ///
    /// A rejected move or draw claim leaves the game in
    /// [`GameStatus::Invalid`], in which [`Self::poll`] reports
    /// [`SessionUpdate::Unavailable`] until every invalid event is resolved.
    /// This convenience delegates to [`Game::resolve_latest_invalid`] so
    /// callers need not destructure the session with [`Self::into_parts`].
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError`] when no invalid event is pending.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, GameSession, GameStatus, Player, Square};
    ///
    /// let mut session =
    ///     GameSession::new(Player::human(), Player::human());
    /// session.white_mut().submit(ChessMove::new(Square::E7, Square::E5))?;
    /// assert!(session.poll().is_err());
    /// assert!(matches!(session.status(), GameStatus::Invalid { .. }));
    /// session.resolve_latest_invalid()?;
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
    pub fn resolve_latest_invalid(&mut self) -> Result<HistoryStep, HistoryError> {
        self.game.resolve_latest_invalid()
    }

    /// Claims an available draw on behalf of the side to move.
    ///
    /// Delegates to [`Game::claim_draw`]. An unavailable claim is recorded as
    /// invalid history and must then be resolved with
    /// [`Self::resolve_latest_invalid`].
    ///
    /// # Errors
    ///
    /// Returns [`DrawClaimError`] when the claim is unavailable; the failed
    /// claim is still recorded as invalid history and blocks polling until
    /// [`Self::resolve_latest_invalid`] clears it.
    pub fn claim_draw(&mut self, claim: DrawClaim) -> Result<(), DrawClaimError> {
        self.game.claim_draw(claim)
    }

    /// Claims a draw by announcing a legal move that would make it available.
    ///
    /// Delegates to [`Game::claim_draw_after`] without applying the announced
    /// move.
    ///
    /// # Errors
    ///
    /// Returns [`DrawClaimError`] when the announced move would not make the
    /// claim available; the failed claim is recorded as invalid history and
    /// must be cleared with [`Self::resolve_latest_invalid`].
    pub fn claim_draw_after(
        &mut self,
        chess_move: ChessMove,
        claim: DrawClaim,
    ) -> Result<(), DrawClaimError> {
        self.game.claim_draw_after(chess_move, claim)
    }

    /// Polls only the player that owns the side to move.
    ///
    /// Human and online players return immediately when no submitted move is
    /// available. Computer players search synchronously. Ready moves are
    /// committed through [`Game::play`], preserving authoritative validation,
    /// history, logging, and terminal adjudication.
    ///
    /// Recovery: while the game is [`Invalid`](GameStatus::Invalid) or
    /// terminal, no player is polled and
    /// [`Unavailable`](SessionUpdate::Unavailable) is returned. Clear
    /// rejections with [`resolve_latest_invalid`](Self::resolve_latest_invalid)
    /// and unavailable draw claims with the same recovery path before
    /// polling again.
    ///
    /// # Errors
    ///
    /// Returns [`SessionError::Player`] when the polled player's synchronous
    /// search or translation fails, and [`SessionError::MoveRejected`] when
    /// the staged move is rejected by [`Game::play`]; the rejection is
    /// recorded as invalid history that blocks later polls until resolved.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Color, GameSession, Player, SessionUpdate};
    ///
    /// let mut session =
    ///     GameSession::new(Player::human(), Player::human());
    /// let update = session.poll()?;
    /// assert!(matches!(
    ///     update,
    ///     SessionUpdate::Pending { player: Color::White }
    /// ));
    /// # Ok::<(), chess::SessionError>(())
    /// ```
    pub fn poll(&mut self) -> Result<SessionUpdate, SessionError> {
        let status = self.game.status();
        if matches!(status, GameStatus::Invalid { .. }) || status.is_terminal() {
            return Ok(SessionUpdate::Unavailable(status));
        }

        let player = self.game.side_to_move();
        let view = PlayerView::new(&self.game);
        let response = match player {
            Color::White => self.white.poll(view),
            Color::Black => self.black.poll(view),
        }
        .map_err(|error| SessionError::Player { player, error })?;

        match response {
            PlayerResponse::Pending => Ok(SessionUpdate::Pending { player }),
            PlayerResponse::Move(chess_move) => {
                let step = self
                    .game
                    .play(chess_move)
                    .map_err(|error| SessionError::MoveRejected { player, error })?;
                Ok(SessionUpdate::MovePlayed { player, step })
            }
        }
    }
}
