use std::io::ErrorKind;

/// The result of a completed write to the output-only SPI LED chain.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SPIEvent {
    bytes: Vec<u8>,
    result: Result<(), ErrorKind>,
}

impl SPIEvent {
    pub const fn new(bytes: Vec<u8>, result: Result<(), ErrorKind>) -> Self {
        Self { bytes, result }
    }

    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }

    pub const fn result(&self) -> &Result<(), ErrorKind> {
        &self.result
    }
}
