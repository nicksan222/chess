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

/// SSD1309 command bytes, named after the controller datasheet.
mod command {
    pub(super) const DISPLAY_OFF: u8 = 0xAE;
    pub(super) const DISPLAY_ON: u8 = 0xAF;
    pub(super) const SET_COMMAND_LOCK: u8 = 0xFD;
    pub(super) const COMMAND_LOCK_UNLOCKED: u8 = 0x12;
    pub(super) const SET_MEMORY_ADDRESSING: u8 = 0x20;
    pub(super) const PAGE_ADDRESSING: u8 = 0x02;
    pub(super) const LOW_COLUMN_START: u8 = 0x00;
    pub(super) const HIGH_COLUMN_START: u8 = 0x10;
    pub(super) const START_LINE_ZERO: u8 = 0x40;
    pub(super) const SET_CONTRAST: u8 = 0x81;
    pub(super) const CONTRAST: u8 = 0xBF;
    pub(super) const SEGMENT_REMAP: u8 = 0xA1;
    pub(super) const NORMAL_DISPLAY: u8 = 0xA6;
    pub(super) const SET_MULTIPLEX_RATIO: u8 = 0xA8;
    pub(super) const MULTIPLEX_64: u8 = 0x3F;
    pub(super) const COM_SCAN_REMAPPED: u8 = 0xC8;
    pub(super) const SET_DISPLAY_OFFSET: u8 = 0xD3;
    pub(super) const NO_OFFSET: u8 = 0x00;
    pub(super) const SET_CLOCK_DIVIDE: u8 = 0xD5;
    pub(super) const CLOCK_DIVIDE: u8 = 0xA0;
    pub(super) const SET_PRECHARGE: u8 = 0xD9;
    pub(super) const PRECHARGE: u8 = 0xF1;
    pub(super) const SET_COM_PINS: u8 = 0xDA;
    pub(super) const COM_PINS: u8 = 0x12;
    pub(super) const SET_VCOMH: u8 = 0xDB;
    pub(super) const VCOMH: u8 = 0x34;
    pub(super) const RESUME_FROM_RAM: u8 = 0xA4;
    /// OR-ed with the page number to select a page.
    pub(super) const PAGE_START: u8 = 0xB0;
}

/// I2C control byte announcing that command bytes follow.
const CONTROL_COMMAND: u8 = 0x00;
/// I2C control byte announcing that display data bytes follow.
const CONTROL_DATA: u8 = 0x40;
/// The longest command sequence sent in one packet.
const MAX_COMMAND_BYTES: usize = 3;
/// Display data bytes per I2C write; the packet adds one control byte.
const CHUNK: usize = 32;
/// Size of the page-major framebuffer.
const FRAME_BYTES: usize = WIDTH as usize * HEIGHT as usize / 8;

/// The power-on sequence from the supplier's init file. SSD1309 uses the
/// module's external OLED supply, not an SSD1306 charge pump.
const INIT: [&[u8]; 14] = [
    &[command::DISPLAY_OFF],
    &[command::SET_COMMAND_LOCK, command::COMMAND_LOCK_UNLOCKED],
    &[command::SET_MEMORY_ADDRESSING, command::PAGE_ADDRESSING],
    &[
        command::LOW_COLUMN_START,
        command::HIGH_COLUMN_START,
        command::START_LINE_ZERO,
    ],
    &[command::SET_CONTRAST, command::CONTRAST],
    &[command::SEGMENT_REMAP, command::NORMAL_DISPLAY],
    &[command::SET_MULTIPLEX_RATIO, command::MULTIPLEX_64],
    &[command::COM_SCAN_REMAPPED],
    &[command::SET_DISPLAY_OFFSET, command::NO_OFFSET],
    &[command::SET_CLOCK_DIVIDE, command::CLOCK_DIVIDE],
    &[command::SET_PRECHARGE, command::PRECHARGE],
    &[command::SET_COM_PINS, command::COM_PINS],
    &[command::SET_VCOMH, command::VCOMH],
    &[
        command::RESUME_FROM_RAM,
        command::NORMAL_DISPLAY,
        command::DISPLAY_ON,
    ],
];

pub(super) struct Controller<I2C> {
    bus: I2C,
    frame: [u8; FRAME_BYTES],
}

pub(super) fn new<I2C: I2c>(bus: I2C) -> Controller<I2C> {
    Controller {
        bus,
        frame: [0; FRAME_BYTES],
    }
}

impl<I2C: I2c> Controller<I2C> {
    pub(super) fn init(&mut self) -> Result<(), DisplayError> {
        for commands in INIT {
            self.commands(commands)?;
        }
        self.clear_buffer();
        Ok(())
    }

    fn commands(&mut self, commands: &[u8]) -> Result<(), DisplayError> {
        if commands.len() > MAX_COMMAND_BYTES {
            return Err(DisplayError::DataFormatNotImplemented);
        }
        let mut packet = [CONTROL_COMMAND; MAX_COMMAND_BYTES + 1];
        packet[1..=commands.len()].copy_from_slice(commands);
        self.bus
            .write(I2C_ADDRESS, &packet[..=commands.len()])
            .map_err(|_| DisplayError::BusWriteError)
    }

    pub(super) fn clear_buffer(&mut self) {
        self.frame.fill(0);
    }

    pub(super) fn flush(&mut self) -> Result<(), DisplayError> {
        // Select each page explicitly: correctness never depends on the previous
        // flush or on where a failed transaction left the controller's cursor.
        for page in 0..HEIGHT / 8 {
            self.commands(&[
                command::PAGE_START | page,
                command::LOW_COLUMN_START,
                command::HIGH_COLUMN_START,
            ])?;
            let offset = usize::from(page) * usize::from(WIDTH);
            for bytes in self.frame[offset..offset + usize::from(WIDTH)].chunks(CHUNK) {
                let mut packet = [CONTROL_DATA; CHUNK + 1];
                packet[1..=bytes.len()].copy_from_slice(bytes);
                self.bus
                    .write(I2C_ADDRESS, &packet[..=bytes.len()])
                    .map_err(|_| DisplayError::BusWriteError)?;
            }
        }
        Ok(())
    }

    pub(super) fn set_display_on(&mut self, enabled: bool) -> Result<(), DisplayError> {
        self.commands(&[if enabled {
            command::DISPLAY_ON
        } else {
            command::DISPLAY_OFF
        }])
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
            let (Ok(x), Ok(y)) = (usize::try_from(point.x), usize::try_from(point.y)) else {
                continue;
            };
            if x >= usize::from(WIDTH) || y >= usize::from(HEIGHT) {
                continue;
            }
            let index = (y / 8) * usize::from(WIDTH) + x;
            let mask = 1 << (y % 8);
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
