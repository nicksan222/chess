//! Turns a bank's confirmed occupancy change into piece events.

use super::HallBank;
use crate::hardware::PieceEvent;

/// A bank's occupancy before and after a confirmed change, one bit per channel.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Change {
    pub before: u8,
    pub after: u8,
}

impl Change {
    /// One event per channel that changed, in channel order.
    pub fn events(self, bank: HallBank) -> impl Iterator<Item = PieceEvent> {
        let changed = self.before ^ self.after;
        bank.squares()
            .iter()
            .enumerate()
            .filter(move |&(channel, _)| changed & (1 << channel) != 0)
            .map(move |(channel, &square)| {
                if self.after & (1 << channel) != 0 {
                    PieceEvent::Placed(square)
                } else {
                    PieceEvent::Removed(square)
                }
            })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hardware::square;

    #[test]
    fn only_changed_channels_become_events_in_channel_order() {
        let [first, ..] = HallBank::all();
        let change = Change {
            before: 0b0000_0011,
            after: 0b1000_0010,
        };
        let events: Vec<_> = change.events(first).collect();
        assert_eq!(
            events,
            [
                PieceEvent::Removed(square!(A1)),
                PieceEvent::Placed(square!(D2))
            ]
        );
    }
}
