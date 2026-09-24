//! Linux GPIO character-device reader for the board's pull-up button inputs.

use std::{collections::HashMap, collections::hash_map::Entry, path::PathBuf};

use gpiocdev::{
    Request,
    line::{Bias, Value},
};

use super::pins::{GPIO, Level, ReadLevel};

/// Keeps one kernel input request per BCM-numbered line on the selected chip.
/// The caller chooses the chip: GPIO numbering is chip-relative, not global.
/// Requests the Pi's internal pull-up; the button shorts the input to ground.
/// This reader does not invert the level; button presses are wired active-low.
pub struct LinuxGpioReader {
    chip: PathBuf,
    pull_up: bool,
    requests: HashMap<u8, Request>,
}

impl LinuxGpioReader {
    pub fn new(chip: impl Into<PathBuf>) -> Self {
        Self {
            chip: chip.into(),
            pull_up: true,
            requests: HashMap::new(),
        }
    }

    /// Use external bias instead of the chip's internal pull-up. `gpio-sim`
    /// injects its own levels this way; the physical panel uses `new`.
    pub fn with_external_bias(chip: impl Into<PathBuf>) -> Self {
        Self {
            chip: chip.into(),
            pull_up: false,
            requests: HashMap::new(),
        }
    }
}

impl ReadLevel for LinuxGpioReader {
    type Error = gpiocdev::Error;

    fn read_level(&mut self, gpio: GPIO) -> Result<Level, Self::Error> {
        let request = match self.requests.entry(gpio.bcm_number()) {
            Entry::Occupied(entry) => entry.into_mut(),
            Entry::Vacant(entry) => {
                let mut builder = Request::builder();
                builder
                    .on_chip(&self.chip)
                    .with_consumer("firmware-button")
                    .with_line(u32::from(gpio.bcm_number()))
                    .as_input();
                if self.pull_up {
                    builder.with_bias(Bias::PullUp);
                }
                entry.insert(builder.request()?)
            }
        };
        match request.lone_value()? {
            Value::Active => Ok(Level::High),
            Value::Inactive => Ok(Level::Low),
        }
    }
}
