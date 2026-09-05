use super::{Gpio, Input, InputOutput, Output, Pin};

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
