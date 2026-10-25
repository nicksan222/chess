//! Reads one bank, configuring it first and recovering it after faults.

use std::fmt::Debug;

use embedded_hal::i2c::I2c;
use logger::{info, warn};

use super::{
    HallBank,
    tca9554::{self, BankError},
};

/// One bank's connection state.
pub struct Monitor {
    bank: HallBank,
    configured: bool,
    faulted: bool,
}

impl Monitor {
    pub const fn new(bank: HallBank) -> Self {
        Self {
            bank,
            configured: false,
            faulted: false,
        }
    }

    pub const fn bank(&self) -> HallBank {
        self.bank
    }

    /// Reads the bank's occupancy, one bit per channel, or `None` if it is
    /// unknown. An expander that lost power or failed a read is configured
    /// again before it is trusted.
    pub fn read<I: I2c>(&mut self, i2c: &mut I) -> Option<u8> {
        let address = self.bank.address();
        if !self.configured {
            if let Err(error) = tca9554::configure(i2c, address) {
                return self.fail(&error);
            }
            self.configured = true;
        }
        let levels = match tca9554::read_inputs(i2c, address) {
            Ok(levels) => levels,
            Err(error) => {
                self.configured = false;
                return self.fail(&error);
            }
        };
        if self.faulted {
            self.faulted = false;
            info!(
                "Hall bank {} at {address:#04x} recovered; reconciling its squares",
                self.bank.label()
            );
        }
        // The sensors pull a channel low when a piece is present.
        Some(!levels)
    }

    /// Logged once per run of failures; the bank's squares become unknown.
    fn fail<E: Debug>(&mut self, error: &BankError<E>) -> Option<u8> {
        if !self.faulted {
            warn!(
                "Hall bank {} at {:#04x} failed: {error}; its squares are unknown until it recovers",
                self.bank.label(),
                self.bank.address()
            );
        }
        self.faulted = true;
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hardware::{hall::fake::Expanders, square};

    #[test]
    fn configures_once_then_reads_occupancy_as_set_bits() {
        let mut expanders = Expanders::new();
        expanders.place(square!(B1));
        let mut monitor = Monitor::new(HallBank::all()[0]);

        assert_eq!(monitor.read(&mut expanders), Some(0b0000_0010));
        assert_eq!(monitor.read(&mut expanders), Some(0b0000_0010));
        assert_eq!(expanders.settings().len(), 2);
    }

    #[test]
    fn a_failed_read_is_unknown_and_forces_reconfiguration() {
        let mut expanders = Expanders::new();
        let mut monitor = Monitor::new(HallBank::all()[1]);
        monitor.read(&mut expanders);

        expanders.absent[1] = true;
        assert_eq!(monitor.read(&mut expanders), None);
        assert_eq!(monitor.read(&mut expanders), None);

        // It returns with arbitrary settings, which must be rewritten.
        expanders.absent[1] = false;
        expanders.registers[1][3] = 0x00;
        expanders.writes.clear();
        assert_eq!(monitor.read(&mut expanders), Some(0));
        assert_eq!(
            expanders.settings(),
            [(0x21, vec![0x03, 0xFF]), (0x21, vec![0x02, 0x00])]
        );
    }
}
