/// An explicit two-state value for persisted settings and controls.
///
/// Unlike `bool`, the variants preserve the meaning of the state at call sites
/// and in pattern matches.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum Toggle {
    /// The setting or capability is disabled.
    #[default]
    Off,
    /// The setting or capability is enabled.
    On,
}

impl Toggle {
    /// Returns the opposite state.
    #[must_use]
    pub const fn toggled(self) -> Self {
        match self {
            Self::Off => Self::On,
            Self::On => Self::Off,
        }
    }

    /// Changes this value to its opposite state.
    pub const fn toggle(&mut self) {
        *self = self.toggled();
    }

    /// Returns whether this value is [`Toggle::On`].
    #[must_use]
    pub const fn is_on(self) -> bool {
        matches!(self, Self::On)
    }

    /// Returns whether this value is [`Toggle::Off`].
    #[must_use]
    pub const fn is_off(self) -> bool {
        matches!(self, Self::Off)
    }
}

impl From<bool> for Toggle {
    fn from(value: bool) -> Self {
        if value { Self::On } else { Self::Off }
    }
}

impl From<Toggle> for bool {
    fn from(value: Toggle) -> Self {
        value.is_on()
    }
}
