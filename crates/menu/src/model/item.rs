use super::Menu;

/// One selectable menu entry.
#[derive(Debug, Eq, PartialEq)]
pub enum MenuItem<'a, A> {
    /// An entry that produces an application-defined action when activated.
    Action {
        /// Text presented for the entry.
        label: &'a str,
        /// Value returned to the application on activation.
        action: A,
    },
    /// An entry that emits an action and blocks further input until completion.
    BlockingAction {
        /// Text presented for the entry.
        label: &'a str,
        /// Value returned when the blocking operation starts.
        action: A,
        /// Value returned when escape aborts the blocking operation.
        escape_action: A,
    },
    /// An entry that opens another menu when activated.
    Submenu {
        /// Text presented for the entry.
        label: &'a str,
        /// Child menu opened on activation.
        menu: &'a Menu<'a, A>,
    },
}

impl<'a, A> MenuItem<'a, A> {
    /// Creates an entry that emits `action` when activated.
    pub const fn action(label: &'a str, action: A) -> Self {
        Self::Action { label, action }
    }

    /// Creates an entry that blocks after emitting `action`.
    ///
    /// While blocked, escape emits `escape_action`. Successful external work
    /// calls [`MenuState::unblock`](crate::MenuState::unblock) instead.
    pub const fn blocking_action(label: &'a str, action: A, escape_action: A) -> Self {
        Self::BlockingAction {
            label,
            action,
            escape_action,
        }
    }

    /// Creates an entry that opens `menu` when activated.
    pub const fn submenu(label: &'a str, menu: &'a Menu<'a, A>) -> Self {
        Self::Submenu { label, menu }
    }

    /// Returns the text presented for this entry.
    pub const fn label(&self) -> &'a str {
        match self {
            Self::Action { label, .. }
            | Self::BlockingAction { label, .. }
            | Self::Submenu { label, .. } => label,
        }
    }

    /// Returns the action carried by this entry, if it is an action entry.
    pub const fn as_action(&self) -> Option<&A> {
        match self {
            Self::Action { action, .. } | Self::BlockingAction { action, .. } => Some(action),
            Self::Submenu { .. } => None,
        }
    }

    /// Returns the action emitted when escape aborts a blocking operation.
    pub const fn escape_action(&self) -> Option<&A> {
        match self {
            Self::BlockingAction { escape_action, .. } => Some(escape_action),
            Self::Action { .. } | Self::Submenu { .. } => None,
        }
    }

    /// Returns whether activation starts a blocking operation.
    pub const fn is_blocking(&self) -> bool {
        matches!(self, Self::BlockingAction { .. })
    }

    /// Returns the child menu carried by this entry, if it is a submenu entry.
    pub const fn as_submenu(&self) -> Option<&'a Menu<'a, A>> {
        match self {
            Self::Action { .. } | Self::BlockingAction { .. } => None,
            Self::Submenu { menu, .. } => Some(menu),
        }
    }
}
