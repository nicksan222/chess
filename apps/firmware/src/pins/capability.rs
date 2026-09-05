/// Runtime representation of a pin's compile-time capability.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum CapabilityKind {
    Input,
    Output,
    InputOutput,
}

impl CapabilityKind {
    pub const fn can_read(self) -> bool {
        matches!(self, Self::Input | Self::InputOutput)
    }

    pub const fn can_write(self) -> bool {
        matches!(self, Self::Output | Self::InputOutput)
    }
}

/// Associates a mode marker with its runtime representation.
pub trait Capability {
    const KIND: CapabilityKind;
}

#[derive(Debug, Eq, Hash, PartialEq)]
pub struct Input;

#[derive(Debug, Eq, Hash, PartialEq)]
pub struct Output;

#[derive(Debug, Eq, Hash, PartialEq)]
pub struct InputOutput;

impl Capability for Input {
    const KIND: CapabilityKind = CapabilityKind::Input;
}

impl Capability for Output {
    const KIND: CapabilityKind = CapabilityKind::Output;
}

impl Capability for InputOutput {
    const KIND: CapabilityKind = CapabilityKind::InputOutput;
}

/// Implemented by modes that may be sampled.
pub trait Readable: Capability {}

/// Implemented by modes that may be driven.
pub trait Writable: Capability {}

impl Readable for Input {}
impl Readable for InputOutput {}
impl Writable for Output {}
impl Writable for InputOutput {}
