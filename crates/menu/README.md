# Menu crate

This crate contains a reusable headless menu state machine. It owns menu
structure, cursor movement, submenu history, and action activation, but
deliberately has no display, GPIO, timing, or operating-system dependency.

An application maps its five controls to `Input`, passes them to
`MenuState`, and renders its read-only `MenuSnapshot` using any display backend.
Actions are values chosen by the application, so this crate does not need to know
what selecting an entry does.

`MenuControls` defines what up, down, left, right, and OK do for each menu.
Bindings can navigate, activate the selected item, return to a parent, emit an
application action, or intentionally do nothing.

Every `MenuItem` is either an action or a submenu. A submenu is a complete
`Menu`, with its own entries and controls. The chessboard tree nests game
choices and destructive confirmations, and returning to a parent restores its
previous cursor.

For behavior that depends on the running application, `ExternalBehavior` can
optionally override a press. `MenuState::handle_with` passes it an immutable
external context and a read-only menu snapshot. A chess game can therefore be
borrowed directly while a behavior object separately owns mutable hardware or
adapter state. Returning `None` falls back to the menu's normal controls.

## Chessboard definition

The concrete product menu is intentionally small:

```text
Main Menu
├── Start Game
│   ├── 1 vs 1
│   └── 1 vs Online
├── Network
│   ├── Status
│   ├── Set Up Network
│   └── Forget Network
│       └── Confirm Forget
└── Reset Game
    └── Confirm Reset
```

The menu emits typed `ChessboardAction` values. Firmware owns game startup,
network status and provisioning, forgetting credentials, and game reset. The
destructive actions require confirmation; pressing left cancels by returning to
the parent menu.

## Effects and ownership

The state machine never executes an action. It reports menu-owned actions as
`Event::Activated(&A)` and externally created actions as
`Event::ExternalAction(A)`. Firmware decides how those values affect hardware or
the game.

Menu definitions and navigation state borrow their data. External behavior gets
`&C`, never ownership or mutable access to application context. This keeps a
running game independent from menu and hardware lifetimes.

## Deliberate constraints

Navigation is non-wrapping and submenu history is allocation-free with a fixed
depth of eight. Empty menus are valid and ignore movement and activation.
Presentation details such as fonts, scrolling, icons, and OLED layout belong in
a renderer rather than this model.
