# Architecture

## Purpose

Record the intended top-level boundaries without fixing their interfaces.

## Known direction

```text
        Physical Board
              |
              v
        Shared Protocol
              |
              v
          Bridge Core
              |
              v
         Local Adapter
```

Offline chess behavior is the initial focus. Integration-specific code stays in
adapter directories, allowing additional adapters to be introduced without
changing bridge core or shared crates. The physical board does not know about
external services, shared crates do not depend on adapter implementations, and
hardware details do not leak unnecessarily into domain crates.

## TODO

Design interfaces and dependency rules in focused future work after concrete
offline requirements are established.
