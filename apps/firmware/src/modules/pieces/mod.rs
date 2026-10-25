//! Piece presence on the board, as observed by the Hall sensors.
//!
//! A module without menu items: it only observes [`PieceEvent`]s. Presence is
//! physical; which chess piece stands where belongs to game logic.

use tokio::sync::watch;

use super::{
    MissingDependency, Never,
    module::{Context, Module},
};
use crate::hardware::{BoardPosition, HardwareEvent, PieceEvent};

/// The module needs no settings.
pub type Settings = ();

/// The module has no menu items.
pub type Request = Never;

/// Which squares hold a piece, and the latest observation.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct Status {
    last: Option<PieceEvent>,
    /// One bit per square, at `row * 8 + column`.
    occupied: u64,
}

impl Status {
    /// The most recent piece observation, if any.
    pub const fn last(&self) -> Option<PieceEvent> {
        self.last
    }

    /// Whether a piece was last seen standing at `position`.
    pub const fn is_occupied(&self, position: BoardPosition) -> bool {
        self.occupied & Self::bit(position) != 0
    }

    /// How many squares hold a piece.
    pub const fn count(&self) -> u32 {
        self.occupied.count_ones()
    }

    fn observe(&mut self, event: PieceEvent) {
        match event {
            PieceEvent::Placed(position) => self.occupied |= Self::bit(position),
            PieceEvent::Removed(position) => self.occupied &= !Self::bit(position),
        }
        self.last = Some(event);
    }

    const fn bit(position: BoardPosition) -> u64 {
        1 << (position.row() * BoardPosition::SIZE + position.column())
    }
}

/// Current piece presence, for other modules.
#[derive(Clone, Debug)]
pub struct Pieces {
    status: watch::Receiver<Status>,
}

impl Pieces {
    /// Presence as of the latest processed piece event.
    pub fn status(&self) -> Status {
        *self.status.borrow()
    }
}

/// The pieces module's engine.
pub(super) struct Engine {
    status: watch::Sender<Status>,
}

impl Module for Engine {
    type Settings = Settings;
    type Status = Status;
    type Request = Request;
    type Facade = Pieces;

    fn new((): &Settings, _: &Context<'_, Status>) -> Result<Self, MissingDependency> {
        Ok(Self {
            status: watch::Sender::new(Status::default()),
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
            self.status.send_replace(*status);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn placing_and_removing_tracks_every_square() {
        let mut status = Status::default();
        for row in 0..BoardPosition::SIZE {
            for column in 0..BoardPosition::SIZE {
                let position = BoardPosition::new(row, column).unwrap();
                status.observe(PieceEvent::Placed(position));
                assert!(status.is_occupied(position));
                assert_eq!(status.last(), Some(PieceEvent::Placed(position)));
            }
        }
        assert_eq!(status.count(), 64);

        let corner = BoardPosition::new(7, 7).unwrap();
        status.observe(PieceEvent::Removed(corner));
        assert!(!status.is_occupied(corner));
        assert_eq!(status.count(), 63);
        assert_eq!(status.last(), Some(PieceEvent::Removed(corner)));
    }
}
