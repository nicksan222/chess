//! Helpers that turn captured I2C traffic back into frames and screenshots.

use std::{fs, path::PathBuf};

use embedded_graphics::{Pixel, geometry::Size, pixelcolor::BinaryColor, prelude::*};
use embedded_graphics_simulator::{OutputSettingsBuilder, SimulatorDisplay};
use firmware::hardware::display::{Display, HEIGHT, WIDTH};

use crate::bus::{BUFFER_SIZE, COMMAND, CapturingI2C, DATA};

pub(crate) fn initialized_display(bus: &CapturingI2C) -> Display<CapturingI2C> {
    let mut display = Display::new(bus.clone());
    display.initialize().unwrap();
    bus.clear();
    display
}

pub(crate) fn transmitted_frame(bus: &CapturingI2C) -> Vec<u8> {
    bus.writes
        .borrow()
        .iter()
        .filter_map(|(_, packet)| packet.strip_prefix(&[DATA]))
        .flatten()
        .copied()
        .collect()
}

pub(crate) fn command_bytes(writes: &[(u8, Vec<u8>)]) -> Vec<u8> {
    writes
        .iter()
        .filter_map(|(_, packet)| packet.strip_prefix(&[COMMAND]))
        .flatten()
        .copied()
        .collect()
}

pub(crate) fn display_from_i2c(bus: &CapturingI2C) -> SimulatorDisplay<BinaryColor> {
    let frame = transmitted_frame(bus);
    assert_eq!(frame.len(), BUFFER_SIZE);
    display_from_frame(&frame)
}

pub(crate) fn display_from_frame(frame: &[u8]) -> SimulatorDisplay<BinaryColor> {
    let mut display = SimulatorDisplay::new(panel_size());
    display
        .draw_iter(display.bounding_box().points().map(|point| {
            let x = usize::try_from(point.x).unwrap();
            let y = usize::try_from(point.y).unwrap();
            let byte = frame[(y / 8) * usize::from(WIDTH) + x];
            Pixel(point, BinaryColor::from(byte & (1 << (y % 8)) != 0))
        }))
        .unwrap();
    display
}

pub(crate) fn panel_size() -> Size {
    Size::new(u32::from(WIDTH), u32::from(HEIGHT))
}

pub(crate) fn save_screenshot(name: &str, display: &SimulatorDisplay<BinaryColor>) {
    let directory = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/display/screenshots");
    fs::create_dir_all(&directory).unwrap();

    let settings = OutputSettingsBuilder::new()
        .scale(4)
        .pixel_spacing(1)
        .build();
    display
        .to_rgb_output_image(&settings)
        .save_png(directory.join(format!("{name}.png")))
        .unwrap();
}
