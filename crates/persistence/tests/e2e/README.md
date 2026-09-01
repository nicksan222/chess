# Persistence end-to-end tests

Each concrete backend has a module under `implementations/`. Its module must call
`backend_contract_tests!` with a factory that returns a fresh store. This
instantiates the shared behavioral contract for missing values, binary and empty
data, replacement, undersized buffers, removal, and flushing.

Backend-specific journeys and failure injection live beside that invocation.
The SQLite suite additionally verifies file reopen durability, transactions,
malformed databases, corrupt typed values, backend failures, and typed schema
operations. New backends follow the same layout rather than copying the shared
contract.
