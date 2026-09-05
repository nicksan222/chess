//! GPIOs connected to the chess board.

mod gpio;

pub use gpio::{Input, InputOutput, Level, Output, Pin, ReadLevel, Readable, Writable, WriteLevel};

/// Linux BCM GPIO numbers used by the board.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
#[allow(clippy::upper_case_acronyms)]
pub enum GPIO {
    I2cData = 2,
    I2cClock = 3,
    UpButton = 5,
    DownButton = 6,
    LedData = 10,
    LedClock = 11,
    LeftButton = 12,
    RightButton = 13,
    OkButton = 16,
    ResetButton = 17,
    PassButton = 19,
    FunctionOneButton = 20,
    FunctionTwoButton = 21,
    FunctionThreeButton = 22,
    FunctionFourButton = 23,
    FunctionFiveButton = 24,
}

impl GPIO {
    pub const fn bcm_number(self) -> u8 {
        self as u8
    }
}

/// GPIOs with their allowed operations encoded in their types.
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
    pub const fn get() -> Self {
        Self {
            i2c_data: Pin::new(GPIO::I2cData),
            i2c_clock: Pin::new(GPIO::I2cClock),
            up_button: Pin::new(GPIO::UpButton),
            down_button: Pin::new(GPIO::DownButton),
            led_data: Pin::new(GPIO::LedData),
            led_clock: Pin::new(GPIO::LedClock),
            left_button: Pin::new(GPIO::LeftButton),
            right_button: Pin::new(GPIO::RightButton),
            ok_button: Pin::new(GPIO::OkButton),
            reset_button: Pin::new(GPIO::ResetButton),
            pass_button: Pin::new(GPIO::PassButton),
            function_one_button: Pin::new(GPIO::FunctionOneButton),
            function_two_button: Pin::new(GPIO::FunctionTwoButton),
            function_three_button: Pin::new(GPIO::FunctionThreeButton),
            function_four_button: Pin::new(GPIO::FunctionFourButton),
            function_five_button: Pin::new(GPIO::FunctionFiveButton),
        }
    }
}
