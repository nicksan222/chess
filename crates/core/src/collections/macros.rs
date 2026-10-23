//! Trait implementations shared by every collection in this module.
//!
//! Each collection supplies `new`, `len`, `iter`, and `iter_mut`.
//! These macros derive the remaining standard traits from that surface so the
//! traits observe the collection's own iteration order.

/// Implements `Default`, `Debug`, and borrowing `IntoIterator`.
///
/// `'a` in the iterator types names the borrow of the collection.
macro_rules! impl_sequence_traits {
    (
        impl[$($generics:tt)*] $collection:ty {
            iter: $iter:ty,
            iter_mut: $iter_mut:ty $(,)?
        }
    ) => {
        impl<$($generics)*> Default for $collection {
            fn default() -> Self {
                Self::new()
            }
        }

        impl<$($generics)*> core::fmt::Debug for $collection
        where
            T: core::fmt::Debug,
        {
            fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
                formatter.debug_list().entries(self).finish()
            }
        }

        impl<'a, $($generics)*> IntoIterator for &'a $collection {
            type Item = &'a T;
            type IntoIter = $iter;

            fn into_iter(self) -> Self::IntoIter {
                self.iter()
            }
        }

        impl<'a, $($generics)*> IntoIterator for &'a mut $collection {
            type Item = &'a mut T;
            type IntoIter = $iter_mut;

            fn into_iter(self) -> Self::IntoIter {
                self.iter_mut()
            }
        }
    };
}

/// Implements `PartialEq`, `Eq`, `PartialOrd`, `Ord`, and `Hash` in iteration
/// order, so equal collections hash alike and compare element by element.
macro_rules! impl_iteration_order_traits {
    (impl[$($generics:tt)*] $collection:ty) => {
        impl<$($generics)*> PartialEq for $collection
        where
            T: PartialEq,
        {
            fn eq(&self, other: &Self) -> bool {
                self.len() == other.len() && self.iter().eq(other)
            }
        }

        impl<$($generics)*> Eq for $collection where T: Eq {}

        impl<$($generics)*> PartialOrd for $collection
        where
            T: PartialOrd,
        {
            fn partial_cmp(&self, other: &Self) -> Option<core::cmp::Ordering> {
                self.iter().partial_cmp(other)
            }
        }

        impl<$($generics)*> Ord for $collection
        where
            T: Ord,
        {
            fn cmp(&self, other: &Self) -> core::cmp::Ordering {
                self.iter().cmp(other)
            }
        }

        impl<$($generics)*> core::hash::Hash for $collection
        where
            T: core::hash::Hash,
        {
            fn hash<H: core::hash::Hasher>(&self, state: &mut H) {
                self.len().hash(state);
                for element in self {
                    element.hash(state);
                }
            }
        }
    };
}
