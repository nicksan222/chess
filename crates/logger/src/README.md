# Logger source

The source tree keeps the facade's independent values separate:

- `level.rs` defines severity and filtering;
- `metadata.rs` carries routing and source context;
- `record.rs` combines metadata with allocation-free formatting arguments;
- `logger.rs` defines the externally implemented backend contract;
- `macros.rs` provides filtered, explicit-logger emission macros;
- `implementations/stderr.rs` is the hosted terminal/simulator backend;
- `implementations/systemd.rs` is the Yocto Raspberry Pi journal-stream backend.

There is intentionally no global registration or allocator. The two optional
I/O implementations are isolated behind the `std` feature; the default facade
remains purely `no_std`.
