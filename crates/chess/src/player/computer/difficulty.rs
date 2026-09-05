//! Human-facing computer difficulty levels.

/// A computer opponent difficulty.
///
/// Each level maps to a fixed minimax lookahead depth in the bundled search
/// engine. Cost grows roughly exponentially with depth, so [`Difficulty::Hard`]
/// and [`Difficulty::Expert`] are substantially slower than
/// [`Difficulty::Beginner`]. Polling is synchronous; measure on your target
/// before using high difficulties on latency-sensitive threads.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Difficulty {
    /// Shallowest lookahead and fastest response.
    Beginner,
    /// A forgiving opponent with limited lookahead.
    Easy,
    /// Balanced strength and response time.
    #[default]
    Medium,
    /// Deeper lookahead; noticeably slower than [`Difficulty::Medium`].
    Hard,
    /// Deepest lookahead; slowest and strongest of the preset levels.
    Expert,
}

impl Difficulty {
    /// Returns the engine lookahead depth for this difficulty.
    ///
    /// The mapping is deliberately a `match` rather than a discriminant
    /// cast so renumbering variants cannot silently retune the engine.
    ///
    /// The depth drives the synchronous computer search started by
    /// [`Player::computer`](crate::Player::computer); higher levels cost
    /// roughly exponentially more time on the polling thread.
    pub(super) const fn search_depth(self) -> i32 {
        match self {
            Self::Beginner => 1,
            Self::Easy => 2,
            Self::Medium => 3,
            Self::Hard => 4,
            Self::Expert => 5,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::Difficulty;

    #[test]
    fn depths_increase_with_strength_without_relying_on_discriminants() {
        assert_eq!(Difficulty::Beginner.search_depth(), 1);
        assert_eq!(Difficulty::Easy.search_depth(), 2);
        assert_eq!(Difficulty::Medium.search_depth(), 3);
        assert_eq!(Difficulty::Hard.search_depth(), 4);
        assert_eq!(Difficulty::Expert.search_depth(), 5);
        assert!(Difficulty::Beginner < Difficulty::Expert);
        assert_eq!(Difficulty::default(), Difficulty::Medium);
    }
}
