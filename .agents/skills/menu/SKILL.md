---
name: menu
description: The purpose and outside view of the `menu` crate, a product-neutral menu state machine for a device with a few buttons. Use when building or driving an on-device menu, or deciding where menu-related code belongs.
---

# menu

## What it is for

The menu crate knows how to move through a menu and nothing about what the
menu is for. It turns a handful of inputs (up, down, left, right, OK,
escape) into a clear account of what happened: the selection moved, a
submenu opened, an action was chosen, input is blocked.

The product, meaning its labels, actions, screens and pixels, lives outside.
The crate would fit a coffee machine as well as a chessboard.

## How it thinks

- **It reports; it never acts.** Choosing an item produces an event that
  carries the application's own action value. Running that action is the
  application's job.
- **The definition is the application's.** The menu tree, the labels and
  even the button bindings are supplied from outside.
- **Some actions take time.** A blocking item holds input until the
  application says it is done or the user escapes, and the application
  supplies what escape means.
- **Small and predictable.** No wrapping at the ends, a fixed depth limit,
  no allocation, and empty menus are allowed.

## Using it from outside

1. Describe your menus with `Menu` and `MenuItem` using your own action type.
2. Map physical controls to `Input` and pass them to a `MenuState`.
3. Handle every `Event` that comes back. `MenuCallbacks` makes forgetting a
   case a compile error.
4. Render from the read-only `MenuSnapshot`.
5. When live application state should change what an input does, add an
   `ExternalBehavior`. The application remains the source of truth.

## Where things belong

What the device's menu contains and what its actions do belong to firmware.
Only the general mechanics of navigating a menu belong here.
