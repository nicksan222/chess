use core::fmt;

/// An insertion error that returns the element rejected by a full collection.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CapacityError<T> {
    element: T,
}

impl<T> CapacityError<T> {
    pub(super) const fn new(element: T) -> Self {
        Self { element }
    }

    /// Returns a shared reference to the rejected element.
    #[must_use]
    pub const fn element(&self) -> &T {
        &self.element
    }

    /// Returns an exclusive reference to the rejected element.
    #[must_use]
    pub const fn element_mut(&mut self) -> &mut T {
        &mut self.element
    }

    /// Consumes the error and returns the rejected element.
    #[must_use]
    pub fn into_element(self) -> T {
        self.element
    }
}

impl<T: fmt::Debug> fmt::Debug for CapacityError<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CapacityError")
            .field("element", &self.element)
            .finish()
    }
}

impl<T> fmt::Display for CapacityError<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("collection is at capacity")
    }
}

impl<T: fmt::Debug> core::error::Error for CapacityError<T> {}
