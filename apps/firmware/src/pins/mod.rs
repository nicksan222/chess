//! Raspberry Pi GPIO assignments for the chess board.
//!
//! Keep this map in sync with `hardware/shared/wiring.py`. BCM numbers are
//! Linux GPIO line offsets, not physical header positions.

mod pin;

pub use pin::{Capability, CapabilityKind, Input, InputOutput, Output, Pin, Readable, Writable};

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

/// Typed access to all board pins.
///
/// Moving a field into a driver prevents that particular value from being
/// reused. Opening and exclusive ownership of the Linux GPIO line remains the
/// responsibility of the GPIO backend.
#[derive(Debug, Eq, PartialEq)]
pub struct BoardPins {
    pub i2c_data: Pin<2, InputOutput>,
    pub i2c_clock: Pin<3, InputOutput>,
    pub up_button: Pin<5, Input>,
    pub down_button: Pin<6, Input>,
    pub led_data: Pin<10, Output>,
    pub led_clock: Pin<11, Output>,
    pub left_button: Pin<12, Input>,
    pub right_button: Pin<13, Input>,
    pub ok_button: Pin<16, Input>,
    pub reset_button: Pin<17, Input>,
    pub pass_button: Pin<19, Input>,
    pub function_one_button: Pin<20, Input>,
    pub function_two_button: Pin<21, Input>,
    pub function_three_button: Pin<22, Input>,
    pub function_four_button: Pin<23, Input>,
    pub function_five_button: Pin<24, Input>,
}

impl BoardPins {
    pub const fn new() -> Self {
        Self {
            i2c_data: Pin::new(Gpio::I2cData),
            i2c_clock: Pin::new(Gpio::I2cClock),
            up_button: Pin::new(Gpio::UpButton),
            down_button: Pin::new(Gpio::DownButton),
            led_data: Pin::new(Gpio::LedData),
            led_clock: Pin::new(Gpio::LedClock),
            left_button: Pin::new(Gpio::LeftButton),
            right_button: Pin::new(Gpio::RightButton),
            ok_button: Pin::new(Gpio::OkButton),
            reset_button: Pin::new(Gpio::ResetButton),
            pass_button: Pin::new(Gpio::PassButton),
            function_one_button: Pin::new(Gpio::FunctionOneButton),
            function_two_button: Pin::new(Gpio::FunctionTwoButton),
            function_three_button: Pin::new(Gpio::FunctionThreeButton),
            function_four_button: Pin::new(Gpio::FunctionFourButton),
            function_five_button: Pin::new(Gpio::FunctionFiveButton),
        }
    }
}

impl Default for BoardPins {
    fn default() -> Self {
        Self::new()
    }
}

/// Every connected GPIO, in ascending BCM-number order.
pub const ALL: [Gpio; 16] = [
    Gpio::I2cData,
    Gpio::I2cClock,
    Gpio::UpButton,
    Gpio::DownButton,
    Gpio::LedData,
    Gpio::LedClock,
    Gpio::LeftButton,
    Gpio::RightButton,
    Gpio::OkButton,
    Gpio::ResetButton,
    Gpio::PassButton,
    Gpio::FunctionOneButton,
    Gpio::FunctionTwoButton,
    Gpio::FunctionThreeButton,
    Gpio::FunctionFourButton,
    Gpio::FunctionFiveButton,
];

/// The twelve directly connected, active-low panel buttons.
pub const BUTTONS: [Gpio; 12] = [
    Gpio::UpButton,
    Gpio::DownButton,
    Gpio::LeftButton,
    Gpio::RightButton,
    Gpio::OkButton,
    Gpio::ResetButton,
    Gpio::PassButton,
    Gpio::FunctionOneButton,
    Gpio::FunctionTwoButton,
    Gpio::FunctionThreeButton,
    Gpio::FunctionFourButton,
    Gpio::FunctionFiveButton,
];
