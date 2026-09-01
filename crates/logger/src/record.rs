use core::fmt;

use crate::{Level, Metadata};

/// One log event passed to a [`crate::Logger`].
pub struct Record<'a> {
    metadata: Metadata<'a>,
    arguments: fmt::Arguments<'a>,
}

impl<'a> Record<'a> {
    /// Creates a record from source metadata and a lazily formatted message.
    pub const fn new(metadata: Metadata<'a>, arguments: fmt::Arguments<'a>) -> Self {
        Self {
            metadata,
            arguments,
        }
    }

    /// Returns all source metadata.
    pub const fn metadata(&self) -> &Metadata<'a> {
        &self.metadata
    }

    /// Returns the record severity.
    pub const fn level(&self) -> Level {
        self.metadata.level()
    }

    /// Returns the backend-defined routing target.
    pub const fn target(&self) -> &'a str {
        self.metadata.target()
    }

    /// Returns the source module path when available.
    pub const fn module_path(&self) -> Option<&'a str> {
        self.metadata.module_path()
    }

    /// Returns the source file when available.
    pub const fn file(&self) -> Option<&'a str> {
        self.metadata.file()
    }

    /// Returns the source line when available.
    pub const fn line(&self) -> Option<u32> {
        self.metadata.line()
    }

    /// Returns the allocation-free formatted message.
    pub const fn arguments(&self) -> &fmt::Arguments<'a> {
        &self.arguments
    }
}
