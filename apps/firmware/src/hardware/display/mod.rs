//! Driver for the display installed in the board.

use ::ssd1306::mode::DisplayConfig;
use display_interface::DisplayError;
use embedded_graphics::{
    Pixel,
    draw_target::DrawTarget,
    geometry::{OriginDimensions, Size},
    pixelcolor::BinaryColor,
};
use embedded_hal::i2c::I2c;

mod ssd1306;

/// Width of the installed display in pixels.
pub const WIDTH: u8 = 128;
/// Height of the installed display in pixels.
pub const HEIGHT: u8 = 64;
/// Seven-bit I2C address of the installed display.
pub const I2C_ADDRESS: u8 = 0x3C;

/// Buffered driver for the display installed in the board.
///
/// Construction performs no I/O. Call [`Self::initialize`] before drawing the
/// first frame. Drawing changes the in-memory frame; call [`Self::flush`] to
/// send it to the panel.
pub struct Display<I2C> {
    controller: ssd1306::Controller<I2C>,
}

impl<I2C: I2c> Display<I2C> {
    /// Creates the board display around an exclusive I2C bus handle.
    pub fn new(i2c: I2C) -> Self {
        Self {
            controller: ssd1306::new(i2c),
        }
    }

    /// Initializes the panel and clears its in-memory frame.
    pub fn initialize(&mut self) -> Result<(), DisplayError> {
        self.controller.init()
    }

    /// Sends the in-memory frame to the panel.
    pub fn flush(&mut self) -> Result<(), DisplayError> {
        self.controller.flush()
    }

    /// Clears the in-memory frame without performing I/O.
    pub fn clear_buffer(&mut self) {
        self.controller.clear_buffer();
    }

    /// Turns the panel on or off without changing its in-memory frame.
    pub fn set_power(&mut self, enabled: bool) -> Result<(), DisplayError> {
        self.controller.set_display_on(enabled)
    }
}

impl<I2C: I2c> OriginDimensions for Display<I2C> {
    fn size(&self) -> Size {
        self.controller.size()
    }
}

impl<I2C: I2c> DrawTarget for Display<I2C> {
    type Color = BinaryColor;
    type Error = DisplayError;

    fn draw_iter<T>(&mut self, pixels: T) -> Result<(), Self::Error>
    where
        T: IntoIterator<Item = Pixel<Self::Color>>,
    {
        self.controller.draw_iter(pixels)
    }

    fn clear(&mut self, color: Self::Color) -> Result<(), Self::Error> {
        DrawTarget::clear(&mut self.controller, color)
    }
}
