//! The installed MC242GW's SSD1309, with a page-major monochrome framebuffer.
//!
//! Initialization follows the supplier's `2.42inch_SSD1309_Init.txt`.
//! The module supplies power-on reset; allow 200 ms after power becomes stable
//! before initialization (the Pi's Linux startup already exceeds that delay).

use display_interface::DisplayError;
use embedded_graphics::{
    Pixel,
    draw_target::DrawTarget,
    geometry::{OriginDimensions, Size},
    pixelcolor::BinaryColor,
};
use embedded_hal::i2c::I2c;

use super::{HEIGHT, I2C_ADDRESS, WIDTH};

pub(super) struct Controller<I2C> {
    bus: I2C,
    frame: [u8; WIDTH as usize * HEIGHT as usize / 8],
}

pub(super) fn new<I2C: I2c>(bus: I2C) -> Controller<I2C> {
    Controller {
        bus,
        frame: [0; WIDTH as usize * HEIGHT as usize / 8],
    }
}

impl<I2C: I2c> Controller<I2C> {
    pub(super) fn init(&mut self) -> Result<(), DisplayError> {
        // SSD1309 uses the module's external OLED supply, not an SSD1306 charge pump.
        for commands in [
            &[0xAE][..],
            &[0xFD, 0x12],
            &[0x20, 0x02],
            &[0x00, 0x10, 0x40],
            &[0x81, 0xBF],
            &[0xA1, 0xA6],
            &[0xA8, 0x3F],
            &[0xC8],
            &[0xD3, 0x00],
            &[0xD5, 0xA0],
            &[0xD9, 0xF1],
            &[0xDA, 0x12],
            &[0xDB, 0x34],
            &[0xA4, 0xA6, 0xAF],
        ] {
            self.commands(commands)?;
        }
        self.clear_buffer();
        Ok(())
    }

    fn commands(&mut self, commands: &[u8]) -> Result<(), DisplayError> {
        let mut packet = [0u8; 4];
        packet[1..=commands.len()].copy_from_slice(commands);
        self.bus
            .write(I2C_ADDRESS, &packet[..commands.len() + 1])
            .map_err(|_| DisplayError::BusWriteError)
    }

    pub(super) fn clear_buffer(&mut self) {
        self.frame.fill(0);
    }

    pub(super) fn flush(&mut self) -> Result<(), DisplayError> {
        // Select each page explicitly: correctness never depends on the previous
        // flush or on where a failed transaction left the controller's cursor.
        for page in 0..HEIGHT / 8 {
            self.commands(&[0xB0 | page, 0x00, 0x10])?;
            let offset = usize::from(page) * usize::from(WIDTH);
            for bytes in self.frame[offset..offset + usize::from(WIDTH)].chunks(32) {
                let mut packet = [0x40u8; 33];
                packet[1..].copy_from_slice(bytes);
                self.bus
                    .write(I2C_ADDRESS, &packet)
                    .map_err(|_| DisplayError::BusWriteError)?;
            }
        }
        Ok(())
    }

    pub(super) fn set_display_on(&mut self, enabled: bool) -> Result<(), DisplayError> {
        self.commands(&[if enabled { 0xAF } else { 0xAE }])
    }
}

impl<I2C: I2c> OriginDimensions for Controller<I2C> {
    fn size(&self) -> Size {
        Size::new(u32::from(WIDTH), u32::from(HEIGHT))
    }
}

impl<I2C: I2c> DrawTarget for Controller<I2C> {
    type Color = BinaryColor;
    type Error = DisplayError;

    fn draw_iter<I>(&mut self, pixels: I) -> Result<(), Self::Error>
    where
        I: IntoIterator<Item = Pixel<Self::Color>>,
    {
        for Pixel(point, color) in pixels {
            if point.x < 0
                || point.y < 0
                || point.x >= i32::from(WIDTH)
                || point.y >= i32::from(HEIGHT)
            {
                continue;
            }
            let index = (point.y as usize / 8) * usize::from(WIDTH) + point.x as usize;
            let mask = 1 << (point.y % 8);
            match color {
                BinaryColor::On => self.frame[index] |= mask,
                BinaryColor::Off => self.frame[index] &= !mask,
            }
        }
        Ok(())
    }

    fn clear(&mut self, color: Self::Color) -> Result<(), Self::Error> {
        self.frame
            .fill(if color == BinaryColor::On { 0xFF } else { 0 });
        Ok(())
    }
}
