//! Public values describing claimable and completed draws.

use core::fmt;

/// A draw the side to move may claim.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum DrawClaim {
    /// The same position has occurred at least three times.
    ThreefoldRepetition,
    /// At least fifty moves by each side have passed without a pawn move or capture.
    FiftyMoveRule,
}

impl fmt::Display for DrawClaim {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::ThreefoldRepetition => "threefold repetition",
            Self::FiftyMoveRule => "fifty-move rule",
        })
    }
}

/// The draws currently available to claim.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Hash)]
pub struct DrawClaims {
    threefold_repetition: bool,
    fifty_move_rule: bool,
}

impl DrawClaims {
    /// No draw is available to claim.
    pub const NONE: Self = Self {
        threefold_repetition: false,
        fifty_move_rule: false,
    };

    /// Returns whether no draw is available to claim.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        !self.threefold_repetition && !self.fifty_move_rule
    }

    /// Returns whether `claim` is available.
    #[must_use]
    pub const fn contains(self, claim: DrawClaim) -> bool {
        match claim {
            DrawClaim::ThreefoldRepetition => self.threefold_repetition,
            DrawClaim::FiftyMoveRule => self.fifty_move_rule,
        }
    }

    /// Returns this set with `claim` available.
    #[must_use]
    pub const fn with(mut self, claim: DrawClaim) -> Self {
        match claim {
            DrawClaim::ThreefoldRepetition => self.threefold_repetition = true,
            DrawClaim::FiftyMoveRule => self.fifty_move_rule = true,
        }
        self
    }
}

/// The reason a game ended in a draw.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum DrawReason {
    /// The side to move claimed an available draw.
    Claimed(DrawClaim),
    /// Neither side can possibly deliver checkmate.
    InsufficientMaterial,
    /// The same position occurred five times.
    FivefoldRepetition,
    /// Seventy-five moves by each side passed without a pawn move or capture.
    SeventyFiveMoveRule,
}
