use std::fmt;

/// Why a bank could not be configured or read.
#[derive(Debug, Eq, PartialEq)]
pub enum BankError<E> {
    Bus(E),
    /// A register read back a value other than the one written.
    Register {
        register: u8,
        expected: u8,
        found: u8,
    },
}

impl<E: fmt::Debug> fmt::Display for BankError<E> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Bus(error) => write!(formatter, "I2C error: {error:?}"),
            Self::Register {
                register,
                expected,
                found,
            } => write!(
                formatter,
                "register {register:#04x} reads {found:#04x}, expected {expected:#04x}"
            ),
        }
    }
}

impl<E> From<E> for BankError<E> {
    fn from(error: E) -> Self {
        Self::Bus(error)
    }
}
