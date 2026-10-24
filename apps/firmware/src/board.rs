//! Names of the Linux devices and services this board's firmware depends on.

/// GPIO character device exposing the Pi's BCM-numbered header lines.
pub const GPIO_CHIP: &str = "/dev/gpiochip0";

/// NetworkManager's name for the board's Wi-Fi radio.
pub const WIFI_INTERFACE: &str = "wlan0";

/// Consumer label the kernel shows for lines this process has requested.
pub const GPIO_CONSUMER: &str = "firmware-button";
