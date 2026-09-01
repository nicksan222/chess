use crate::model::{Command, Input};

use super::{BlockingOperation, MenuState};
use crate::navigation::{callbacks::MenuCallbacks, event::Event, external::ExternalBehavior};

impl<'a, A> MenuState<'a, A> {
    /// Applies one input using the current menu's controls.
    ///
    /// While blocked, escape aborts the active operation and every other input
    /// produces [`Event::InputBlocked`].
    pub fn handle(&mut self, input: Input) -> Event<'a, A> {
        if let Some(event) = self.handle_blocking_input(input) {
            return event;
        }

        self.apply_menu_input(input)
    }

    /// Applies input and dispatches every action-bearing event.
    ///
    /// This is the preferred application entry point because the callback type
    /// must implement every method required by [`MenuCallbacks`].
    pub fn handle_and_dispatch<C>(&mut self, input: Input, callbacks: &mut C) -> Event<'a, A>
    where
        C: MenuCallbacks<A> + ?Sized,
    {
        let event = self.handle(input);
        event.dispatch(callbacks);
        event
    }

    /// Applies input with an optional externally defined override.
    ///
    /// `context` is read-only, so a chess game can be passed directly without
    /// transferring ownership. The behavior remains mutable so it can own
    /// stateful hardware adapters. If it returns no command, the menu's normal
    /// controls are used. Blocking state is resolved before the override, so an
    /// external behavior cannot bypass it.
    pub fn handle_with<C, B>(&mut self, input: Input, context: &C, behavior: &mut B) -> Event<'a, A>
    where
        C: ?Sized,
        B: ExternalBehavior<C, A> + ?Sized,
    {
        if let Some(event) = self.handle_blocking_input(input) {
            return event;
        }

        let Some(command) = behavior.on_input(context, self.snapshot(), input) else {
            return self.apply_menu_input(input);
        };

        self.apply_external(command)
    }

    /// Applies externally overridden input and dispatches action-bearing events.
    pub fn handle_with_and_dispatch<C, B, H>(
        &mut self,
        input: Input,
        context: &C,
        behavior: &mut B,
        callbacks: &mut H,
    ) -> Event<'a, A>
    where
        C: ?Sized,
        B: ExternalBehavior<C, A> + ?Sized,
        H: MenuCallbacks<A> + ?Sized,
    {
        let event = self.handle_with(input, context, behavior);
        event.dispatch(callbacks);
        event
    }

    fn handle_blocking_input(&mut self, input: Input) -> Option<Event<'a, A>> {
        let blocking = self.blocking.as_ref()?;

        if input == Input::Escape {
            let operation = blocking.action;
            let escape_action = blocking.escape_action;
            self.blocking = None;
            Some(Event::BlockingAborted {
                operation,
                escape_action,
            })
        } else {
            Some(Event::InputBlocked)
        }
    }

    fn apply_menu_input(&mut self, input: Input) -> Event<'a, A> {
        match self.current.controls().command(input) {
            Command::SelectPrevious => self.previous(),
            Command::SelectNext => self.next(),
            Command::Activate => self.activate(),
            Command::GoBack => self.back(),
            Command::Action(action) => Event::Activated(action),
            Command::Ignore => Event::Ignored,
        }
    }

    fn apply_external(&mut self, command: Command<A>) -> Event<'a, A> {
        match command {
            Command::SelectPrevious => self.previous(),
            Command::SelectNext => self.next(),
            Command::Activate => self.activate(),
            Command::GoBack => self.back(),
            Command::Action(action) => Event::ExternalAction(action),
            Command::Ignore => Event::Ignored,
        }
    }

    pub(super) fn begin_blocking(&mut self, action: &'a A, escape_action: &'a A) -> Event<'a, A> {
        self.blocking = Some(BlockingOperation {
            action,
            escape_action,
        });
        Event::BlockingStarted(action)
    }
}
