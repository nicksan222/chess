use crate::Level;

/// Static context describing a log record before its message is formatted.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct Metadata<'a> {
    level: Level,
    target: &'a str,
    module_path: Option<&'a str>,
    file: Option<&'a str>,
    line: Option<u32>,
}

impl<'a> Metadata<'a> {
    /// Creates record metadata.
    pub const fn new(
        level: Level,
        target: &'a str,
        module_path: Option<&'a str>,
        file: Option<&'a str>,
        line: Option<u32>,
    ) -> Self {
        Self {
            level,
            target,
            module_path,
            file,
            line,
        }
    }

    /// Returns the record severity.
    pub const fn level(&self) -> Level {
        self.level
    }

    /// Returns the backend-defined routing target.
    pub const fn target(&self) -> &'a str {
        self.target
    }

    /// Returns the source module path when available.
    pub const fn module_path(&self) -> Option<&'a str> {
        self.module_path
    }

    /// Returns the source file when available.
    pub const fn file(&self) -> Option<&'a str> {
        self.file
    }

    /// Returns the source line when available.
    pub const fn line(&self) -> Option<u32> {
        self.line
    }
}
