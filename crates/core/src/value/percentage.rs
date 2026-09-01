use core::fmt;

/// A percentage guaranteed to be in the inclusive range `0..=100`.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Percentage(u8);

impl Percentage {
    /// Zero percent.
    pub const ZERO: Self = Self(0);

    /// One hundred percent.
    pub const FULL: Self = Self(100);

    /// Creates a percentage when `value` is in `0..=100`.
    pub const fn new(value: u8) -> Result<Self, InvalidPercentage> {
        if value <= 100 {
            Ok(Self(value))
        } else {
            Err(InvalidPercentage { value })
        }
    }

    /// Returns the numeric percentage.
    #[must_use]
    pub const fn get(self) -> u8 {
        self.0
    }
}

impl TryFrom<u8> for Percentage {
    type Error = InvalidPercentage;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        Self::new(value)
    }
}

impl From<Percentage> for u8 {
    fn from(value: Percentage) -> Self {
        value.get()
    }
}

/// A value outside the inclusive percentage range `0..=100`.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct InvalidPercentage {
    value: u8,
}

impl InvalidPercentage {
    /// Returns the rejected value.
    #[must_use]
    pub const fn value(self) -> u8 {
        self.value
    }
}

impl fmt::Display for InvalidPercentage {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "percentage {} is outside 0..=100", self.value)
    }
}

impl core::error::Error for InvalidPercentage {}
