use crate::model::{Menu, MenuItem};

use super::snapshot::MenuSnapshot;

mod input;
mod traversal;

/// Maximum number of parent menus retained while navigating submenus.
pub const MAX_MENU_DEPTH: usize = 8;

struct Location<'a, A> {
    menu: &'a Menu<'a, A>,
    selected: usize,
}

struct BlockingOperation<'a, A> {
    action: &'a A,
    escape_action: &'a A,
}

/// Current location, cursor, and optional blocking operation within a menu tree.
pub struct MenuState<'a, A> {
    root: &'a Menu<'a, A>,
    current: &'a Menu<'a, A>,
    selected: usize,
    depth: usize,
    blocking: Option<BlockingOperation<'a, A>>,
    history: [Option<Location<'a, A>>; MAX_MENU_DEPTH],
}

impl<'a, A> MenuState<'a, A> {
    /// Starts at the first entry of `root`.
    pub const fn new(root: &'a Menu<'a, A>) -> Self {
        Self {
            root,
            current: root,
            selected: 0,
            depth: 0,
            blocking: None,
            history: [const { None }; MAX_MENU_DEPTH],
        }
    }

    /// Returns the root menu supplied at construction.
    pub const fn root_menu(&self) -> &'a Menu<'a, A> {
        self.root
    }

    /// Returns the menu that a renderer should currently display.
    pub const fn current_menu(&self) -> &'a Menu<'a, A> {
        self.current
    }

    /// Returns the selected zero-based index.
    ///
    /// Empty menus also report zero; use [`Self::selected_item`] to distinguish
    /// that case.
    pub const fn selected_index(&self) -> usize {
        self.selected
    }

    /// Returns the selected entry, or `None` when the current menu is empty.
    pub fn selected_item(&self) -> Option<&'a MenuItem<'a, A>> {
        self.current.items().get(self.selected)
    }

    /// Returns the current submenu depth. The root menu is depth zero.
    pub const fn depth(&self) -> usize {
        self.depth
    }

    /// Returns a read-only view suitable for external behavior and renderers.
    pub const fn snapshot(&self) -> MenuSnapshot<'a, A> {
        let (blocking_action, escape_action) = match &self.blocking {
            Some(blocking) => (Some(blocking.action), Some(blocking.escape_action)),
            None => (None, None),
        };

        MenuSnapshot::new(
            self.current,
            self.selected,
            self.depth,
            blocking_action,
            escape_action,
        )
    }

    /// Returns the action whose operation is currently blocking input.
    pub const fn blocking_action(&self) -> Option<&'a A> {
        match &self.blocking {
            Some(blocking) => Some(blocking.action),
            None => None,
        }
    }

    /// Returns the action emitted if escape aborts the blocking operation.
    pub const fn blocking_escape_action(&self) -> Option<&'a A> {
        match &self.blocking {
            Some(blocking) => Some(blocking.escape_action),
            None => None,
        }
    }

    /// Returns whether a blocking operation is active.
    pub const fn is_blocked(&self) -> bool {
        self.blocking.is_some()
    }

    /// Completes the current blocking operation and restores normal input.
    ///
    /// The returned action identifies the operation that was unblocked. `None`
    /// means no blocking operation was active.
    pub fn unblock(&mut self) -> Option<&'a A> {
        self.blocking.take().map(|blocking| blocking.action)
    }

    /// Returns whether the root menu is currently displayed.
    pub const fn is_at_root(&self) -> bool {
        self.depth == 0
    }
}
