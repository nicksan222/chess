# Persistence source

The source tree separates the backend contract from record framing:

- `store/` defines the byte-oriented backend contract and load outcomes;
- `schema/` defines typed fields, field-operation errors, and key validation;
- `value/` defines codecs and stable implementations for shared value types;
- `record/` provides allocation-free record framing, checksums, and errors;
- `implementations/` contains the opt-in hosted SQLite adapter;
- `macros.rs` generates consumer schemas and ergonomic typed operations;
- `lib.rs` documents and exports the public facade.

No concrete backend lives in this crate. Applications and tests implement the
trait for their platform and pass implementations explicitly to consumers.
