//! Validation of sequence numbers, previous hashes, and event hashes.

use super::{
    super::{HistoryError, HistoryHash, HistoryStep, Ply},
    calculate_hash,
};

/// Checks one step against its expected ply, tip, and cumulative hash.
///
/// Validation is order-sensitive: ply sequencing first, then the
/// anchor-to-tip previous-hash link, then the recomputed commitment. This
/// is the per-link check replayed by
/// [`GameHistory::verify`](crate::GameHistory::verify) and the gate for
/// [`GameHistory::try_append`](crate::GameHistory::try_append).
///
/// # Errors
///
/// Returns [`HistoryError::Ply`](crate::HistoryError) for a skipped or
/// repeated ply, [`HistoryError::PreviousHash`](crate::HistoryError) when
/// the step does not commit to the expected predecessor, and
/// [`HistoryError::Hash`](crate::HistoryError) for a wrong cumulative
/// hash.
pub(in crate::game::history) fn validate_step(
    step: HistoryStep,
    expected_ply: Ply,
    expected_previous: HistoryHash,
) -> Result<(), HistoryError> {
    if step.ply() != expected_ply {
        return Err(HistoryError::Ply {
            expected: expected_ply,
            actual: step.ply(),
        });
    }
    if step.previous_hash() != expected_previous {
        return Err(HistoryError::PreviousHash {
            ply: step.ply(),
            expected: expected_previous,
            actual: step.previous_hash(),
        });
    }
    let expected_hash = calculate_hash(expected_previous, expected_ply, step.event());
    if step.hash() != expected_hash {
        return Err(HistoryError::Hash {
            ply: step.ply(),
            expected: expected_hash,
            actual: step.hash(),
        });
    }
    Ok(())
}
