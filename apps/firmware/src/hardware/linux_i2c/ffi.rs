//! The `i2c-dev` combined-transfer interface from `<linux/i2c-dev.h>` and
//! `<linux/i2c.h>`.

/// `I2C_RDWR`: perform several messages as one combined transfer.
pub const I2C_RDWR: libc::Ioctl = 0x0707;
/// `I2C_M_RD`: the message reads from the target.
pub const I2C_M_RD: u16 = 0x0001;

/// `struct i2c_msg`.
#[repr(C)]
pub struct Message {
    pub address: u16,
    pub flags: u16,
    pub length: u16,
    pub buffer: *mut u8,
}

/// `struct i2c_rdwr_ioctl_data`.
#[repr(C)]
pub struct Transfer {
    pub messages: *mut Message,
    pub count: u32,
}
