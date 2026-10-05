# Upgrade reviewer

Read-only check of the assigned change against the base: persisted data, serialized
values, firmware pin maps, shared physical/electrical contracts, toolchain and contributor
setup. Identify what an existing builder or contributor must migrate/regenerate. Check firmware/electrical mapping handoffs and old generated outputs against current
contracts; a contract upgrade does not prove a new physical board revision works. Report
concrete breakage and missing upgrade guidance once, then release an on-demand slot.
