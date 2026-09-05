# Focused PCB checks

- `board/test_dimensions.py`: board envelope/orientation, every square and bank,
  component alignment, courtyards, pads, and plated slots.
- `board/test_native.py`: native identities survive unrelated insertion and reordering.
- `pipeline/test_build.py`: atomic publication, source-change detection, native report
  failures, and mandatory physical-evidence gating.
- `spice/`: electrical and movement scenarios derived from actual native pad nets.

Accessor, serialization, architecture-policing and frozen-snapshot suites were
intentionally removed. The production pipeline still enforces native ERC/DRC and
schematic parity; `build.physical_evidence()` independently gates fabrication.

Run without publishing:

```sh
PYTHONPATH=hardware python3 -m unittest discover -s hardware/pcb/tests -p 'test_*.py'
```

`just --justfile hardware/pcb/justfile review` regenerates, checks and publishes the
complete native review set, including SPICE circuits. KiCad and ngspice are required.
