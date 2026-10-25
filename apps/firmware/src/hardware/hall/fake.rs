//! Scripted TCA9554s for unit tests: movable pieces, faults and a write log.

use embedded_hal::i2c::{ErrorKind, ErrorType, I2c, NoAcknowledgeSource, Operation};

use super::{FIRST_ADDRESS, HallBank};
use chess::Square;

/// Power-on registers: inputs high, outputs high, no inversion, all inputs.
pub(super) const POWER_ON: [u8; 4] = [0xFF, 0xFF, 0x00, 0xFF];

/// Eight expanders answering at 0x20–0x27.
pub(super) struct Expanders {
    pub(super) registers: [[u8; 4]; HallBank::COUNT],
    /// Banks that do not acknowledge their address.
    pub(super) absent: [bool; HallBank::COUNT],
    pub(super) writes: Vec<(u8, Vec<u8>)>,
}

impl Expanders {
    pub(super) fn new() -> Self {
        Self {
            registers: [POWER_ON; HallBank::COUNT],
            absent: [false; HallBank::COUNT],
            writes: Vec::new(),
        }
    }

    pub(super) fn place(&mut self, square: Square) {
        let (input, bit) = self.input_bit(square);
        *input &= !bit;
    }

    pub(super) fn remove(&mut self, square: Square) {
        let (input, bit) = self.input_bit(square);
        *input |= bit;
    }

    /// Register settings written, in order; pointer-only writes are omitted.
    pub(super) fn settings(&self) -> Vec<(u8, Vec<u8>)> {
        self.writes
            .iter()
            .filter(|(_, bytes)| bytes.len() == 2)
            .cloned()
            .collect()
    }

    /// The input-port register and channel bit reading `square`.
    fn input_bit(&mut self, square: Square) -> (&mut u8, u8) {
        for (bank, registers) in HallBank::all().into_iter().zip(&mut self.registers) {
            if let Some(channel) = bank.squares().iter().position(|&s| s == square) {
                return (&mut registers[0], 1 << channel);
            }
        }
        unreachable!("every square belongs to a bank")
    }
}

#[derive(Debug, Eq, PartialEq)]
pub(super) struct Nack;

impl embedded_hal::i2c::Error for Nack {
    fn kind(&self) -> ErrorKind {
        ErrorKind::NoAcknowledge(NoAcknowledgeSource::Address)
    }
}

impl ErrorType for Expanders {
    type Error = Nack;
}

impl I2c for Expanders {
    fn transaction(
        &mut self,
        address: u8,
        operations: &mut [Operation<'_>],
    ) -> Result<(), Self::Error> {
        let bank = usize::from(address - FIRST_ADDRESS);
        if self.absent[bank] {
            return Err(Nack);
        }
        let mut pointer = 0;
        for operation in operations {
            match operation {
                Operation::Write(bytes) => {
                    self.writes.push((address, bytes.to_vec()));
                    pointer = usize::from(bytes[0]);
                    // The input port is read-only.
                    if let [_, value] = bytes
                        && pointer != 0
                    {
                        self.registers[bank][pointer] = *value;
                    }
                }
                Operation::Read(bytes) => bytes[0] = self.registers[bank][pointer],
            }
        }
        Ok(())
    }
}
