//! Piece presence on the board, as observed by the Hall sensors.
//!
//! A module without menu items: it only observes [`PieceEvent`]s. Presence is
//! physical; which chess piece stands where belongs to game logic.

use chess::{Square, SquareSet};

use crate::events::{StatePublisher, StateSubscription};

use super::{
    MissingDependency, Never,
    module::{Context, Module},
};
use crate::hardware::{HardwareEvent, PieceEvent};

/// The module needs no settings.
pub type Settings = ();

/// The module has no menu items.
pub type Request = Never;

/// Which squares hold a piece, and the latest observation.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct Status {
    last: Option<PieceEvent>,
    occupied: SquareSet,
}

impl Status {
    /// The most recent piece observation, if any.
    pub const fn last(&self) -> Option<PieceEvent> {
        self.last
    }

    /// Whether a piece was last seen standing at `position`.
    pub const fn is_occupied(&self, position: Square) -> bool {
        self.occupied.contains(position)
    }

    /// How many squares hold a piece.
    pub const fn count(&self) -> u32 {
        self.occupied.len().value() as u32
    }

    fn observe(&mut self, event: PieceEvent) {
        match event {
            PieceEvent::Placed(position) => {
                self.occupied.insert(position);
            }
            PieceEvent::Removed(position) => {
                self.occupied.remove(position);
            }
        }
        self.last = Some(event);
    }
}

/// Current piece presence, for other modules.
#[derive(Clone, Debug)]
pub struct Pieces {
    status: StateSubscription<Status>,
}

impl Pieces {
    /// Presence as of the latest processed piece event.
    pub fn status(&self) -> Status {
        self.status.current()
    }
}

/// The pieces module's engine.
pub(super) struct Engine {
    status: StatePublisher<Status>,
}

impl Module for Engine {
    type Settings = Settings;
    type Status = Status;
    type Request = Request;
    type Facade = Pieces;

    fn new((): &Settings, _: &Context<'_, Status>) -> Result<Self, MissingDependency> {
        Ok(Self {
            status: StatePublisher::new(Status::default()),
        })
    }

    fn facade(&self) -> Pieces {
        Pieces {
            status: self.status.subscribe(),
        }
    }

    fn event(&mut self, event: HardwareEvent, status: &mut Status) {
        if let HardwareEvent::Piece(piece) = event {
            status.observe(piece);
            self.status.replace(*status);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn duplicate_observations_preserve_set_membership() {
        let mut status = Status::default();
        for _ in 0..2 {
            status.observe(PieceEvent::Placed(Square::E4));
        }
        assert!(status.is_occupied(Square::E4));
        assert_eq!(status.count(), 1);
        for _ in 0..2 {
            status.observe(PieceEvent::Removed(Square::E4));
        }
        assert!(!status.is_occupied(Square::E4));
        assert_eq!(status.count(), 0);
    }

    #[test]
    fn placing_and_removing_tracks_every_square() {
        let mut status = Status::default();
        for position in Square::all() {
            status.observe(PieceEvent::Placed(position));
            assert!(status.is_occupied(position));
            assert_eq!(status.last(), Some(PieceEvent::Placed(position)));
        }
        assert_eq!(status.count(), 64);

        let corner = Square::H8;
        status.observe(PieceEvent::Removed(corner));
        assert!(!status.is_occupied(corner));
        assert_eq!(status.count(), 63);
        assert_eq!(status.last(), Some(PieceEvent::Removed(corner)));
    }
}
