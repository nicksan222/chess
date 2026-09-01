use crate::model::{Menu, MenuItem};

/// Read-only view of the current menu location.
pub struct MenuSnapshot<'a, A> {
    menu: &'a Menu<'a, A>,
    selected: usize,
    depth: usize,
    blocking_action: Option<&'a A>,
    escape_action: Option<&'a A>,
}

impl<'a, A> MenuSnapshot<'a, A> {
    pub(super) const fn new(
        menu: &'a Menu<'a, A>,
        selected: usize,
        depth: usize,
        blocking_action: Option<&'a A>,
        escape_action: Option<&'a A>,
    ) -> Self {
        Self {
            menu,
            selected,
            depth,
            blocking_action,
            escape_action,
        }
    }

    /// Returns the menu receiving the input.
    pub const fn menu(&self) -> &'a Menu<'a, A> {
        self.menu
    }

    /// Returns the selected zero-based index.
    ///
    /// Empty menus also report zero; use [`Self::selected_item`] to distinguish
    /// that case.
    pub const fn selected_index(&self) -> usize {
        self.selected
    }

    /// Returns the selected item, or `None` for an empty menu.
    pub fn selected_item(&self) -> Option<&'a MenuItem<'a, A>> {
        self.menu.items().get(self.selected)
    }

    /// Returns the current depth, where the root menu is depth zero.
    pub const fn depth(&self) -> usize {
        self.depth
    }

    /// Returns the action whose operation is currently blocking input.
    pub const fn blocking_action(&self) -> Option<&'a A> {
        self.blocking_action
    }

    /// Returns the action emitted if escape aborts the blocking operation.
    pub const fn blocking_escape_action(&self) -> Option<&'a A> {
        self.escape_action
    }

    /// Returns whether a blocking operation is active.
    pub const fn is_blocked(&self) -> bool {
        self.blocking_action.is_some()
    }
}

impl<A> Clone for MenuSnapshot<'_, A> {
    fn clone(&self) -> Self {
        *self
    }
}

impl<A> Copy for MenuSnapshot<'_, A> {}
