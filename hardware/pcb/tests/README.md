# PCB source tests

These tests own all electrical, product, generated-artifact, placement, and
fabrication release requirements. `./tools/pcb` generates the native project,
runs KiCad ERC/DRC, then runs the tests against those outputs. Immediately before
Gerber export it reruns the suite with `PCB_RELEASE=1`, enabling physical Hall
sensor and magnet evidence tests that are skipped during ordinary source review.
