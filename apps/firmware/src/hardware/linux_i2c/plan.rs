//! Lays out an `embedded-hal` transaction as kernel messages.
//!
//! Adjacent operations of the same direction are coalesced into one message,
//! as `embedded-hal` requires them to be sent without a restart between them.

use std::io;

use embedded_hal::i2c::Operation;

use super::{
    LinuxI2cError,
    ffi::{I2C_M_RD, Message},
};

/// One message: the coalesced bytes of adjacent same-direction operations.
struct Run {
    read: bool,
    bytes: Vec<u8>,
}

/// A transaction's messages and where each operation's bytes sit in them.
pub struct Plan {
    runs: Vec<Run>,
    /// Per operation: its run and its offset within that run.
    placements: Vec<(usize, usize)>,
}

impl Plan {
    pub fn new(operations: &[Operation<'_>]) -> Self {
        let mut runs: Vec<Run> = Vec::new();
        let mut placements = Vec::with_capacity(operations.len());
        for operation in operations {
            let (read, bytes) = match operation {
                Operation::Read(buffer) => (true, vec![0; buffer.len()]),
                Operation::Write(bytes) => (false, bytes.to_vec()),
            };
            let last = runs.len().saturating_sub(1);
            match runs.last_mut() {
                Some(run) if run.read == read => {
                    placements.push((last, run.bytes.len()));
                    run.bytes.extend(bytes);
                }
                _ => {
                    placements.push((runs.len(), 0));
                    runs.push(Run { read, bytes });
                }
            }
        }
        Self { runs, placements }
    }

    pub fn is_empty(&self) -> bool {
        self.runs.is_empty()
    }

    /// The kernel messages for this plan, each pointing into its run's bytes.
    /// They stay valid while the plan is alive and not otherwise borrowed.
    pub fn messages(&mut self, address: u8) -> Result<Vec<Message>, LinuxI2cError> {
        self.runs
            .iter_mut()
            .map(|run| {
                let length = u16::try_from(run.bytes.len()).map_err(|_| {
                    LinuxI2cError(io::Error::new(
                        io::ErrorKind::InvalidInput,
                        "I2C message longer than 65535 bytes",
                    ))
                })?;
                Ok(Message {
                    address: u16::from(address),
                    flags: if run.read { I2C_M_RD } else { 0 },
                    length,
                    buffer: run.bytes.as_mut_ptr(),
                })
            })
            .collect()
    }

    /// Copies the bytes the target sent into each read operation's buffer.
    pub fn scatter(&self, operations: &mut [Operation<'_>]) {
        for (operation, &(run, offset)) in operations.iter_mut().zip(&self.placements) {
            if let Operation::Read(buffer) = operation {
                let length = buffer.len();
                buffer.copy_from_slice(&self.runs[run].bytes[offset..offset + length]);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adjacent_operations_of_one_direction_share_a_message() {
        let (mut first, mut second, mut third) = ([0; 1], [0; 2], [0; 1]);
        let mut operations = [
            Operation::Write(&[0x00]),
            Operation::Write(&[0x01, 0x02]),
            Operation::Read(&mut first),
            Operation::Read(&mut second),
            Operation::Write(&[0x03]),
            Operation::Read(&mut third),
        ];
        let mut plan = Plan::new(&operations);
        let shape: Vec<_> = plan
            .runs
            .iter()
            .map(|run| (run.read, run.bytes.clone()))
            .collect();
        assert_eq!(
            shape,
            [
                (false, vec![0x00, 0x01, 0x02]),
                (true, vec![0; 3]),
                (false, vec![0x03]),
                (true, vec![0]),
            ]
        );

        // Stand in for the kernel filling the read messages.
        plan.runs[1].bytes.copy_from_slice(&[0xA1, 0xA2, 0xA3]);
        plan.runs[3].bytes.copy_from_slice(&[0xB1]);
        plan.scatter(&mut operations);
        assert_eq!((first, second, third), ([0xA1], [0xA2, 0xA3], [0xB1]));
    }

    #[test]
    fn messages_flag_reads_and_address_the_target() {
        let mut buffer = [0; 2];
        let mut plan = Plan::new(&[Operation::Write(&[0x00]), Operation::Read(&mut buffer)]);
        let messages = plan.messages(0x27).unwrap();
        let shape: Vec<_> = messages
            .iter()
            .map(|message| (message.address, message.flags, message.length))
            .collect();
        assert_eq!(shape, [(0x27, 0, 1), (0x27, I2C_M_RD, 2)]);
        assert!(Plan::new(&[]).is_empty());
    }
}
