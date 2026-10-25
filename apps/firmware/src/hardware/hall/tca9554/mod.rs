//! The TCA9554 registers the Hall scan uses; see `docs/host.md#reading-the-board`.
//!
//! The device has one 8-bit port. The Output Port register (0x01) is never
//! written: the Hall sensors are open-drain and every pin stays an input.

mod error;

use embedded_hal::i2c::I2c;

pub use error::BankError;

const INPUT_PORT: u8 = 0x00;
const POLARITY_INVERSION: u8 = 0x02;
const CONFIGURATION: u8 = 0x03;
/// Configuration value making all eight pins inputs.
const ALL_INPUTS: u8 = 0xFF;
/// Polarity value reporting every input as its electrical level.
const NO_INVERSION: u8 = 0x00;

/// Makes every pin an uninverted input and confirms both registers took effect.
pub fn configure<I: I2c>(i2c: &mut I, address: u8) -> Result<(), BankError<I::Error>> {
    for (register, value) in [
        (CONFIGURATION, ALL_INPUTS),
        (POLARITY_INVERSION, NO_INVERSION),
    ] {
        i2c.write(address, &[register, value])?;
        let found = read_register(i2c, address, register)?;
        if found != value {
            return Err(BankError::Register {
                register,
                expected: value,
                found,
            });
        }
    }
    Ok(())
}

/// Reads the input port: bit `n` is the electrical level of channel P`n`.
pub fn read_inputs<I: I2c>(i2c: &mut I, address: u8) -> Result<u8, BankError<I::Error>> {
    Ok(read_register(i2c, address, INPUT_PORT)?)
}

/// A command write followed by a repeated-start byte read.
fn read_register<I: I2c>(i2c: &mut I, address: u8, register: u8) -> Result<u8, I::Error> {
    let mut value = [0];
    i2c.write_read(address, &[register], &mut value)?;
    Ok(value[0])
}

#[cfg(test)]
mod tests {
    use std::convert::Infallible;

    use embedded_hal::i2c::{ErrorType, Operation};

    use super::*;
    use crate::hardware::hall::fake::Expanders;

    /// Acknowledges everything but reads zero from every register.
    struct StuckAtZero;

    impl ErrorType for StuckAtZero {
        type Error = Infallible;
    }

    impl I2c for StuckAtZero {
        fn transaction(
            &mut self,
            _: u8,
            operations: &mut [Operation<'_>],
        ) -> Result<(), Infallible> {
            for operation in operations {
                if let Operation::Read(bytes) = operation {
                    bytes.fill(0x00);
                }
            }
            Ok(())
        }
    }

    #[test]
    fn configuration_writes_inputs_then_polarity_and_never_the_output_port() {
        let mut expanders = Expanders::new();
        configure(&mut expanders, 0x24).unwrap();
        assert_eq!(
            expanders.settings(),
            [(0x24, vec![0x03, 0xFF]), (0x24, vec![0x02, 0x00])]
        );
        assert_eq!(read_inputs(&mut expanders, 0x24), Ok(0xFF));
    }

    #[test]
    fn a_register_that_does_not_take_its_value_fails_configuration() {
        assert_eq!(
            configure(&mut StuckAtZero, 0x20),
            Err(BankError::Register {
                register: 0x03,
                expected: 0xFF,
                found: 0x00
            })
        );
    }
}
