# Core crate

This crate contains small, integration-neutral building blocks shared by the
workspace. Additions must have a concrete consumer, documented invariants, and
no dependency on hardware or application adapters.

The crate is `no_std`, while its owned collections currently require an
allocator. Fixed-capacity collections should be preferred by allocator-free
firmware.
