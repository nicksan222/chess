/// Application callbacks for every action-bearing menu event.
///
/// The trait deliberately provides no default implementations. Applications
/// using [`Event::dispatch`](crate::Event::dispatch) must decide how immediate
/// actions, blocking starts, and blocking aborts are handled.
pub trait MenuCallbacks<A> {
    /// Handles an immediate menu action.
    fn on_action(&mut self, action: &A);

    /// Starts external work for a blocking action.
    ///
    /// The menu remains blocked until [`MenuState::unblock`](crate::MenuState::unblock)
    /// is called or the player presses escape.
    fn on_blocking_started(&mut self, action: &A);

    /// Aborts external work after the player presses escape.
    ///
    /// `operation` identifies the action that started the work, while
    /// `escape_action` defines the operation-specific cancellation callback.
    fn on_blocking_aborted(&mut self, operation: &A, escape_action: &A);
}
