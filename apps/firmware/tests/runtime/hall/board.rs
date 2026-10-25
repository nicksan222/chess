//! The eight expanders as one scripted board, shared with the test so it can
//! move pieces while the production poller owns the bus.

use std::{
    convert::Infallible,
    sync::{Arc, Mutex},
};

use chess::Square;

use embedded_hal::i2c::{ErrorType, I2c, Operation};
use firmware::hardware::hall::{FIRST_ADDRESS, HallBank};

/// Input-port levels of the eight expanders.
#[derive(Clone)]
pub(super) struct Board(Arc<Mutex<[u8; HallBank::COUNT]>>);

impl Board {
    pub(super) fn empty() -> Self {
        Self(Arc::new(Mutex::new([0xFF; HallBank::COUNT])))
    }

    pub(super) fn place(&self, name: &str) {
        self.update(name, |input, bit| input & !bit);
    }

    pub(super) fn remove(&self, name: &str) {
        self.update(name, |input, bit| input | bit);
    }

    /// Applies `change` to the input port and channel bit that read `name`.
    fn update(&self, name: &str, change: impl Fn(u8, u8) -> u8) {
        let square = square(name);
        let mut inputs = self.0.lock().unwrap();
        for (bank, input) in HallBank::all().into_iter().zip(inputs.iter_mut()) {
            if let Some(channel) = bank.squares().iter().position(|&s| s == square) {
                *input = change(*input, 1 << channel);
            }
        }
    }
}

impl ErrorType for Board {
    type Error = Infallible;
}

/// Answers every register read with what configuration expects, and the input
/// port with the current levels.
impl I2c for Board {
    fn transaction(
        &mut self,
        address: u8,
        operations: &mut [Operation<'_>],
    ) -> Result<(), Self::Error> {
        let mut register = 0;
        for operation in operations {
            match operation {
                Operation::Write(bytes) => register = bytes[0],
                Operation::Read(bytes) => {
                    bytes[0] = match register {
                        0x00 => self.0.lock().unwrap()[usize::from(address - FIRST_ADDRESS)],
                        0x02 => 0x00,
                        _ => 0xFF,
                    }
                }
            }
        }
        Ok(())
    }
}

pub(super) fn square(name: &str) -> Square {
    name.parse().unwrap()
}
