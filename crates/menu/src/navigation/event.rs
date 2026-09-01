use super::callbacks::MenuCallbacks;

/// Observable result of applying input to a menu state.
#[must_use = "menu events may contain actions that the application must handle"]
#[derive(Debug, Eq, PartialEq)]
pub enum Event<'a, A> {
    /// The selected entry changed.
    SelectionChanged {
        /// New zero-based index within the current menu.
        selected: usize,
    },
    /// A child menu was opened.
    Opened {
        /// New depth, where the root menu is depth zero.
        depth: usize,
    },
    /// The parent menu was restored.
    Closed {
        /// New depth, where the root menu is depth zero.
        depth: usize,
    },
    /// An action stored in a menu or its controls was requested.
    Activated(&'a A),
    /// A blocking operation started and must be completed externally.
    BlockingStarted(&'a A),
    /// Escape aborted a blocking operation.
    BlockingAborted {
        /// Action that originally started the operation.
        operation: &'a A,
        /// Action configured for escape.
        escape_action: &'a A,
    },
    /// Input was ignored because a blocking operation is active.
    InputBlocked,
    /// An action produced by external behavior was requested.
    ExternalAction(A),
    /// The command could not change the current state.
    Ignored,
    /// A submenu could not open because the navigation depth limit was reached.
    DepthLimitReached,
}

impl<A> Event<'_, A> {
    /// Dispatches every action-bearing event to the required callback.
    ///
    /// Navigation-only events do not invoke application callbacks.
    pub fn dispatch<C>(&self, callbacks: &mut C)
    where
        C: MenuCallbacks<A> + ?Sized,
    {
        match self {
            Self::Activated(action) => callbacks.on_action(action),
            Self::ExternalAction(action) => callbacks.on_action(action),
            Self::BlockingStarted(action) => callbacks.on_blocking_started(action),
            Self::BlockingAborted {
                operation,
                escape_action,
            } => callbacks.on_blocking_aborted(operation, escape_action),
            Self::SelectionChanged { .. }
            | Self::Opened { .. }
            | Self::Closed { .. }
            | Self::InputBlocked
            | Self::Ignored
            | Self::DepthLimitReached => {}
        }
    }
}
