# Core crate

This crate contains small, integration-neutral building blocks shared by the
workspace, including collections, byte-oriented persistence capabilities, and
versioned checksummed record envelopes. Additions must have a concrete
consumer, documented invariants, and no dependency on hardware or application
adapters.

The crate is `no_std`. Its linked list, queue, and growable stack require an
allocator; fixed-capacity collections are available for allocator-free targets.
The linked list is the storage primitive for the chess crate's hash-linked move
history.
