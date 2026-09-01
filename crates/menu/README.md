# Menu crate

This crate contains a reusable headless menu state machine. It owns menu
structure, cursor movement, submenu history, and action activation, but
deliberately has no display, GPIO, timing, or operating-system dependency.

An application maps navigation, confirmation, and escape controls to `Input`,
passes them to `MenuState`, and renders its read-only `MenuSnapshot` using any
display backend. Actions are values chosen by the application, so the reusable
model does not need to know
what selecting an entry does.

`MenuControls` defines what up, down, left, right, OK, and escape do for each
menu. Bindings can navigate, activate the selected item, return to a parent,
emit an application action, or intentionally do nothing.

Every `MenuItem` is an immediate action, a blocking action with dedicated escape
behavior, or a submenu. A submenu is a complete
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
│   └── 1 vs Online (escape cancels)
├── Network
│   ├── Status
│   ├── Set Up Network
│   └── Forget Network
│       └── Confirm Forget
└── Reset Game
    └── Confirm Reset
```

The menu emits typed `ChessboardAction` values. Firmware owns game startup,
network status and provisioning, forgetting credentials, and game reset. Online
startup blocks menu input until firmware calls `MenuState::unblock`; escape emits
`CancelOnlineGame` and unlocks immediately. Destructive actions require
confirmation, and pressing left cancels by returning to the parent menu.

## Effects and ownership

`ChessboardCallbacks` has no default methods, so firmware must explicitly
implement every concrete menu action. Its blanket `MenuCallbacks` integration
routes immediate actions and blocking starts to their callback, and routes a
blocking escape to the entry's dedicated escape callback. Each blocking entry
defines both its start action and its escape action.

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
