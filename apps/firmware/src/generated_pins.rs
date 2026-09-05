// @generated from pcbnew's native board model; do not edit.

/// A Raspberry Pi GPIO that the native PCB connects.
///
/// This trait describes only host pin identity. Consumers provide the concrete
/// GPIO implementation and assign application meaning to each marker type.
pub trait RaspberryPiPin {
    /// Broadcom GPIO line number used by Linux GPIO interfaces.
    const BCM_NUMBER: u8;

    /// Physical position on the Raspberry Pi 40-pin header.
    const HEADER_PIN: u8;
}

/// BCM GPIO 2, on physical header pin 3.
///
/// The current PCB net is `I2C_SDA`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio2;

impl RaspberryPiPin for Gpio2 {
    const BCM_NUMBER: u8 = 2;
    const HEADER_PIN: u8 = 3;
}

/// BCM GPIO 3, on physical header pin 5.
///
/// The current PCB net is `I2C_SCL`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio3;

impl RaspberryPiPin for Gpio3 {
    const BCM_NUMBER: u8 = 3;
    const HEADER_PIN: u8 = 5;
}

/// BCM GPIO 5, on physical header pin 29.
///
/// The current PCB net is `BTN_UP`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio5;

impl RaspberryPiPin for Gpio5 {
    const BCM_NUMBER: u8 = 5;
    const HEADER_PIN: u8 = 29;
}

/// BCM GPIO 6, on physical header pin 31.
///
/// The current PCB net is `BTN_DOWN`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio6;

impl RaspberryPiPin for Gpio6 {
    const BCM_NUMBER: u8 = 6;
    const HEADER_PIN: u8 = 31;
}

/// BCM GPIO 10, on physical header pin 19.
///
/// The current PCB net is `SPI_DATA_3V3`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio10;

impl RaspberryPiPin for Gpio10 {
    const BCM_NUMBER: u8 = 10;
    const HEADER_PIN: u8 = 19;
}

/// BCM GPIO 11, on physical header pin 23.
///
/// The current PCB net is `SPI_CLK_3V3`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio11;

impl RaspberryPiPin for Gpio11 {
    const BCM_NUMBER: u8 = 11;
    const HEADER_PIN: u8 = 23;
}

/// BCM GPIO 12, on physical header pin 32.
///
/// The current PCB net is `BTN_LEFT`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio12;

impl RaspberryPiPin for Gpio12 {
    const BCM_NUMBER: u8 = 12;
    const HEADER_PIN: u8 = 32;
}

/// BCM GPIO 13, on physical header pin 33.
///
/// The current PCB net is `BTN_RIGHT`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio13;

impl RaspberryPiPin for Gpio13 {
    const BCM_NUMBER: u8 = 13;
    const HEADER_PIN: u8 = 33;
}

/// BCM GPIO 16, on physical header pin 36.
///
/// The current PCB net is `BTN_OK`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio16;

impl RaspberryPiPin for Gpio16 {
    const BCM_NUMBER: u8 = 16;
    const HEADER_PIN: u8 = 36;
}

/// BCM GPIO 17, on physical header pin 11.
///
/// The current PCB net is `BTN_RESET`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio17;

impl RaspberryPiPin for Gpio17 {
    const BCM_NUMBER: u8 = 17;
    const HEADER_PIN: u8 = 11;
}

/// BCM GPIO 19, on physical header pin 35.
///
/// The current PCB net is `BTN_PASS`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio19;

impl RaspberryPiPin for Gpio19 {
    const BCM_NUMBER: u8 = 19;
    const HEADER_PIN: u8 = 35;
}

/// BCM GPIO 20, on physical header pin 38.
///
/// The current PCB net is `BTN_F1`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio20;

impl RaspberryPiPin for Gpio20 {
    const BCM_NUMBER: u8 = 20;
    const HEADER_PIN: u8 = 38;
}

/// BCM GPIO 21, on physical header pin 40.
///
/// The current PCB net is `BTN_F2`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio21;

impl RaspberryPiPin for Gpio21 {
    const BCM_NUMBER: u8 = 21;
    const HEADER_PIN: u8 = 40;
}

/// BCM GPIO 22, on physical header pin 15.
///
/// The current PCB net is `BTN_F3`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio22;

impl RaspberryPiPin for Gpio22 {
    const BCM_NUMBER: u8 = 22;
    const HEADER_PIN: u8 = 15;
}

/// BCM GPIO 23, on physical header pin 16.
///
/// The current PCB net is `BTN_F4`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio23;

impl RaspberryPiPin for Gpio23 {
    const BCM_NUMBER: u8 = 23;
    const HEADER_PIN: u8 = 16;
}

/// BCM GPIO 24, on physical header pin 18.
///
/// The current PCB net is `BTN_F5`. Firmware decides what that net means.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub struct Gpio24;

impl RaspberryPiPin for Gpio24 {
    const BCM_NUMBER: u8 = 24;
    const HEADER_PIN: u8 = 18;
}
