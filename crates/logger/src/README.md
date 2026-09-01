# Logger source

The source tree keeps the facade's independent values separate:

- `level.rs` defines severity and filtering;
- `metadata.rs` carries routing and source context;
- `record.rs` combines metadata with allocation-free formatting arguments;
- `logger.rs` defines the externally implemented backend contract;
- `macros.rs` provides filtered macros backed by the global registry;
- `registry.rs` safely stores the optional process-wide logger;
- `implementations/stderr.rs` is the hosted terminal/simulator backend;
- `implementations/systemd.rs` is the Yocto Raspberry Pi journal-stream backend.

Global registration is allocation-free and optional. The two I/O
implementations remain isolated behind the `std` feature; the default facade
and registry are purely `no_std`.
