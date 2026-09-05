use super::CapabilityKind;

#[derive(Clone, Copy)]
struct Metadata {
    name: &'static str,
    bcm: u8,
    header: u8,
    capability: CapabilityKind,
    active_low: bool,
}

/// Every GPIO connection between the Raspberry Pi and the PCB.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum Gpio {
    I2cData,
    I2cClock,
    UpButton,
    DownButton,
    LedData,
    LedClock,
    LeftButton,
    RightButton,
    OkButton,
    ResetButton,
    PassButton,
    FunctionOneButton,
    FunctionTwoButton,
    FunctionThreeButton,
    FunctionFourButton,
    FunctionFiveButton,
}

impl Gpio {
    /// Every connected GPIO, in ascending BCM-number order.
    pub const ALL: [Self; 16] = [
        Self::I2cData,
        Self::I2cClock,
        Self::UpButton,
        Self::DownButton,
        Self::LedData,
        Self::LedClock,
        Self::LeftButton,
        Self::RightButton,
        Self::OkButton,
        Self::ResetButton,
        Self::PassButton,
        Self::FunctionOneButton,
        Self::FunctionTwoButton,
        Self::FunctionThreeButton,
        Self::FunctionFourButton,
        Self::FunctionFiveButton,
    ];

    /// The twelve directly connected, active-low panel buttons.
    pub const BUTTONS: [Self; 12] = [
        Self::UpButton,
        Self::DownButton,
        Self::LeftButton,
        Self::RightButton,
        Self::OkButton,
        Self::ResetButton,
        Self::PassButton,
        Self::FunctionOneButton,
        Self::FunctionTwoButton,
        Self::FunctionThreeButton,
        Self::FunctionFourButton,
        Self::FunctionFiveButton,
    ];

    const fn metadata(self) -> Metadata {
        use CapabilityKind::{Input, InputOutput, Output};

        match self {
            Self::I2cData => Metadata::new("I2C data", 2, 3, InputOutput, false),
            Self::I2cClock => Metadata::new("I2C clock", 3, 5, InputOutput, false),
            Self::UpButton => Metadata::new("up button", 5, 29, Input, true),
            Self::DownButton => Metadata::new("down button", 6, 31, Input, true),
            Self::LedData => Metadata::new("LED data", 10, 19, Output, false),
            Self::LedClock => Metadata::new("LED clock", 11, 23, Output, false),
            Self::LeftButton => Metadata::new("left button", 12, 32, Input, true),
            Self::RightButton => Metadata::new("right button", 13, 33, Input, true),
            Self::OkButton => Metadata::new("OK button", 16, 36, Input, true),
            Self::ResetButton => Metadata::new("reset button", 17, 11, Input, true),
            Self::PassButton => Metadata::new("pass button", 19, 35, Input, true),
            Self::FunctionOneButton => Metadata::new("function one button", 20, 38, Input, true),
            Self::FunctionTwoButton => Metadata::new("function two button", 21, 40, Input, true),
            Self::FunctionThreeButton => {
                Metadata::new("function three button", 22, 15, Input, true)
            }
            Self::FunctionFourButton => Metadata::new("function four button", 23, 16, Input, true),
            Self::FunctionFiveButton => Metadata::new("function five button", 24, 18, Input, true),
        }
    }

    pub const fn name(self) -> &'static str {
        self.metadata().name
    }

    pub const fn bcm_number(self) -> u8 {
        self.metadata().bcm
    }

    pub const fn header_pin(self) -> u8 {
        self.metadata().header
    }

    pub const fn capability(self) -> CapabilityKind {
        self.metadata().capability
    }

    pub const fn can_read(self) -> bool {
        self.capability().can_read()
    }

    pub const fn can_write(self) -> bool {
        self.capability().can_write()
    }

    pub const fn is_active_low(self) -> bool {
        self.metadata().active_low
    }
}

impl Metadata {
    const fn new(
        name: &'static str,
        bcm: u8,
        header: u8,
        capability: CapabilityKind,
        active_low: bool,
    ) -> Self {
        Self {
            name,
            bcm,
            header,
            capability,
            active_low,
        }
    }
}
