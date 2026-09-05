//! Raspberry Pi GPIO assignments for the chess board.
//!
//! Keep these declarations in sync with `hardware/shared/wiring.py` and the
//! native PCB host connections. BCM numbers are Linux GPIO line offsets, not
//! physical header positions.

/// How the PCB allows firmware to use a GPIO.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum Capability {
    /// Firmware may only sample the line.
    Input,
    /// Firmware may only drive the line.
    Output,
    /// Firmware may both sample and drive the line.
    InputOutput,
}

impl Capability {
    /// Whether this capability permits sampling the line.
    pub const fn can_read(self) -> bool {
        matches!(self, Self::Input | Self::InputOutput)
    }

    /// Whether this capability permits driving the line.
    pub const fn can_write(self) -> bool {
        matches!(self, Self::Output | Self::InputOutput)
    }
}

/// A named GPIO connection between the Raspberry Pi and the PCB.
///
/// `Gpio` is a small, copyable hardware descriptor. GPIO backends can accept it
/// without duplicating board-specific numbers throughout the firmware.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct Gpio {
    name: &'static str,
    bcm_number: u8,
    header_pin: u8,
    capability: Capability,
    active_low: bool,
}

impl Gpio {
    /// Defines a GPIO assignment.
    pub const fn new(
        name: &'static str,
        bcm_number: u8,
        header_pin: u8,
        capability: Capability,
        active_low: bool,
    ) -> Self {
        assert!(!name.is_empty(), "GPIO name must not be empty");
        assert!(bcm_number <= 27, "invalid Raspberry Pi Zero GPIO number");
        assert!(header_pin >= 1 && header_pin <= 40, "invalid header pin");

        Self {
            name,
            bcm_number,
            header_pin,
            capability,
            active_low,
        }
    }

    /// Human-readable board function used in diagnostics.
    pub const fn name(self) -> &'static str {
        self.name
    }

    /// Broadcom GPIO number (the line offset used by Linux GPIO APIs).
    pub const fn bcm_number(self) -> u8 {
        self.bcm_number
    }

    /// Physical position on the Raspberry Pi 40-pin header.
    pub const fn header_pin(self) -> u8 {
        self.header_pin
    }

    /// Operations permitted by the PCB connection.
    pub const fn capability(self) -> Capability {
        self.capability
    }

    /// Whether firmware may sample this connection.
    pub const fn can_read(self) -> bool {
        self.capability.can_read()
    }

    /// Whether firmware may drive this connection.
    pub const fn can_write(self) -> bool {
        self.capability.can_write()
    }

    /// Whether a low electrical level represents the asserted logical state.
    pub const fn is_active_low(self) -> bool {
        self.active_low
    }
}

/// I²C data for the Hall-sensor expanders and OLED.
pub const I2C_DATA: Gpio = Gpio::new("I2C data", 2, 3, Capability::InputOutput, false);
/// I²C clock for the Hall-sensor expanders and OLED.
pub const I2C_CLOCK: Gpio = Gpio::new("I2C clock", 3, 5, Capability::InputOutput, false);
/// Up navigation button; electrically active low.
pub const UP_BUTTON: Gpio = Gpio::new("up button", 5, 29, Capability::Input, true);
/// Down navigation button; electrically active low.
pub const DOWN_BUTTON: Gpio = Gpio::new("down button", 6, 31, Capability::Input, true);
/// SPI data driven into the SK9822 LED chain's level buffer.
pub const LED_DATA: Gpio = Gpio::new("LED data", 10, 19, Capability::Output, false);
/// SPI clock driven into the SK9822 LED chain's level buffer.
pub const LED_CLOCK: Gpio = Gpio::new("LED clock", 11, 23, Capability::Output, false);
/// Left navigation button; electrically active low.
pub const LEFT_BUTTON: Gpio = Gpio::new("left button", 12, 32, Capability::Input, true);
/// Right navigation button; electrically active low.
pub const RIGHT_BUTTON: Gpio = Gpio::new("right button", 13, 33, Capability::Input, true);
/// OK/confirm button; electrically active low.
pub const OK_BUTTON: Gpio = Gpio::new("OK button", 16, 36, Capability::Input, true);
/// Reset button; electrically active low.
pub const RESET_BUTTON: Gpio = Gpio::new("reset button", 17, 11, Capability::Input, true);
/// Pass-turn button; electrically active low.
pub const PASS_BUTTON: Gpio = Gpio::new("pass button", 19, 35, Capability::Input, true);
/// First context-sensitive function button; electrically active low.
pub const FUNCTION_ONE_BUTTON: Gpio =
    Gpio::new("function one button", 20, 38, Capability::Input, true);
/// Second context-sensitive function button; electrically active low.
pub const FUNCTION_TWO_BUTTON: Gpio =
    Gpio::new("function two button", 21, 40, Capability::Input, true);
/// Third context-sensitive function button; electrically active low.
pub const FUNCTION_THREE_BUTTON: Gpio =
    Gpio::new("function three button", 22, 15, Capability::Input, true);
/// Fourth context-sensitive function button; electrically active low.
pub const FUNCTION_FOUR_BUTTON: Gpio =
    Gpio::new("function four button", 23, 16, Capability::Input, true);
/// Fifth context-sensitive function button; electrically active low.
pub const FUNCTION_FIVE_BUTTON: Gpio =
    Gpio::new("function five button", 24, 18, Capability::Input, true);

/// Every GPIO connected by the PCB, in ascending BCM-number order.
pub const ALL: [Gpio; 16] = [
    I2C_DATA,
    I2C_CLOCK,
    UP_BUTTON,
    DOWN_BUTTON,
    LED_DATA,
    LED_CLOCK,
    LEFT_BUTTON,
    RIGHT_BUTTON,
    OK_BUTTON,
    RESET_BUTTON,
    PASS_BUTTON,
    FUNCTION_ONE_BUTTON,
    FUNCTION_TWO_BUTTON,
    FUNCTION_THREE_BUTTON,
    FUNCTION_FOUR_BUTTON,
    FUNCTION_FIVE_BUTTON,
];

/// The twelve directly connected, active-low panel buttons.
pub const BUTTONS: [Gpio; 12] = [
    UP_BUTTON,
    DOWN_BUTTON,
    LEFT_BUTTON,
    RIGHT_BUTTON,
    OK_BUTTON,
    RESET_BUTTON,
    PASS_BUTTON,
    FUNCTION_ONE_BUTTON,
    FUNCTION_TWO_BUTTON,
    FUNCTION_THREE_BUTTON,
    FUNCTION_FOUR_BUTTON,
    FUNCTION_FIVE_BUTTON,
];
