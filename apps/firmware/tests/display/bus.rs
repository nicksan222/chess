//! Fake I2C buses: one records writes, one dies after a few.

use core::convert::Infallible;
use std::{cell::RefCell, rc::Rc};

use embedded_hal::i2c::{Error as I2cError, ErrorKind, ErrorType, I2c, Operation};
use firmware::hardware::display::{HEIGHT, WIDTH};

pub(crate) const COMMAND: u8 = 0x00;
pub(crate) const DATA: u8 = 0x40;
pub(crate) const BUFFER_SIZE: usize = WIDTH as usize * HEIGHT as usize / 8;

pub(crate) type I2CWrites = Rc<RefCell<Vec<(u8, Vec<u8>)>>>;

#[derive(Clone, Default)]
pub(crate) struct CapturingI2C {
    pub(crate) writes: I2CWrites,
}

impl CapturingI2C {
    pub(crate) fn clear(&self) {
        self.writes.borrow_mut().clear();
    }
}

impl ErrorType for CapturingI2C {
    type Error = Infallible;
}

impl I2c for CapturingI2C {
    fn transaction(
        &mut self,
        address: u8,
        operations: &mut [Operation<'_>],
    ) -> Result<(), Self::Error> {
        for operation in operations {
            match operation {
                Operation::Write(bytes) => self.writes.borrow_mut().push((address, bytes.to_vec())),
                Operation::Read(bytes) => bytes.fill(0),
            }
        }
        Ok(())
    }
}

/// A bus that stops answering after `accepted` write operations.
pub(crate) struct DyingI2C {
    pub(crate) accepted: usize,
}

#[derive(Debug)]
pub(crate) struct BusDown;

impl I2cError for BusDown {
    fn kind(&self) -> ErrorKind {
        ErrorKind::Other
    }
}

impl ErrorType for DyingI2C {
    type Error = BusDown;
}

impl I2c for DyingI2C {
    fn transaction(&mut self, _: u8, _: &mut [Operation<'_>]) -> Result<(), Self::Error> {
        if self.accepted == 0 {
            return Err(BusDown);
        }
        self.accepted -= 1;
        Ok(())
    }
}
