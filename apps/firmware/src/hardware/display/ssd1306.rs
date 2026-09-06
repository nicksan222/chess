use embedded_hal::i2c::I2c;
use ssd1306::{
    I2CDisplayInterface, Ssd1306,
    mode::BufferedGraphicsMode,
    prelude::{DisplayRotation, DisplaySize128x64, I2CInterface},
};

pub(super) type Controller<I2C> =
    Ssd1306<I2CInterface<I2C>, DisplaySize128x64, BufferedGraphicsMode<DisplaySize128x64>>;

pub(super) fn new<I2C: I2c>(i2c: I2C) -> Controller<I2C> {
    Ssd1306::new(
        I2CDisplayInterface::new(i2c),
        DisplaySize128x64,
        DisplayRotation::Rotate0,
    )
    .into_buffered_graphics_mode()
}
