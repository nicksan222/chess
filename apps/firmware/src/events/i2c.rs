use std::io::ErrorKind;

/// A logical operation performed on the board's shared I2C bus.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum I2COperation {
    Read { bytes: Vec<u8> },
    Write { bytes: Vec<u8> },
    WriteRead { written: Vec<u8>, read: Vec<u8> },
}

/// The result of a completed I2C operation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct I2CEvent {
    address: u8,
    operation: I2COperation,
    result: Result<(), ErrorKind>,
}

impl I2CEvent {
    /// Records a completed operation against a seven-bit I2C address.
    pub fn new(address: u8, operation: I2COperation, result: Result<(), ErrorKind>) -> Self {
        assert!(address <= 0x7f, "I2C addresses are seven bits");
        Self {
            address,
            operation,
            result,
        }
    }

    pub const fn address(&self) -> u8 {
        self.address
    }

    pub const fn operation(&self) -> &I2COperation {
        &self.operation
    }

    pub const fn result(&self) -> &Result<(), ErrorKind> {
        &self.result
    }
}
