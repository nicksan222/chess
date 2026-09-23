# Menu crate

This crate is a reusable `no_std` headless menu state machine. It owns menu
primitives, cursor movement, submenu history, externally configured blocking
operations, and observable state changes. It deliberately contains no product
menu, screen catalog, display, GPIO, timing, networking, or operating-system
code.

Applications compose `Menu`, `MenuItem`, and `MenuControls` in their own
definition. Labels and action values are application-owned. An action may be
immediate or blocking; blocking entries also receive an application-provided
escape action. The crate executes none of them.

```rust
use menu::{Menu, MenuItem};

#[derive(Debug, Eq, PartialEq)]
enum Action {
    OpenSettings,
    StartUpdate,
    CancelUpdate,
}

static ROOT: Menu<'static, Action> = Menu::new(
    "Main Menu",
    &[
        MenuItem::action("Settings", Action::OpenSettings),
        MenuItem::blocking_action(
            "Update",
            Action::StartUpdate,
            Action::CancelUpdate,
        ),
    ],
);
```

## Interaction boundary

An application maps physical controls to `Input`, passes them to `MenuState`,
and renders its read-only `MenuSnapshot`. The result is an `Event` describing a
selection change, navigation change, or externally defined action.

`MenuControls` makes every input binding part of the external definition. The
conventional list configuration uses up/down to select, right/OK to activate,
and left/escape to return. Definitions can replace every binding.

Blocking behavior is also externally supplied. Activating a blocking item emits
`Event::BlockingStarted` and captures input. External code either completes it
with `MenuState::unblock` or lets escape emit `Event::BlockingAborted` with the
configured cancellation action.

For behavior that depends on live application state, `ExternalBehavior` may
override an input using immutable application context and a read-only menu
snapshot. The application remains the source of truth.

## Deliberate constraints

Navigation is non-wrapping and submenu history is allocation-free with a fixed
depth of eight. Empty menus are valid. Presentation details such as fonts,
scrolling, icons, and pixels belong in an external renderer.
