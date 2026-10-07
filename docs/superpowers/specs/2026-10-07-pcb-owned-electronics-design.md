# Shared specifications and PCB-dependent CAD generation

## Agreed direction

Keep readable shared supplier dimensions, named mounting interfaces and layout
values where both PCB and CAD need them. Removing shared definitions would make
ordinary access to these values harder without eliminating the need to author
them. Do not infer holes, contact positions or display areas from Blender meshes.

The main PCB, including its substrate, copper, holes, artwork and mounted
components, is rendered by KiCad into an importable GLB. CAD consumes that
checked export rather than building a second representation. Shared specifications
remain the source for enclosure fits and off-board assembly geometry.

## Scope

The existing PCB export/import pipeline already provides this model dependency.
Preserve it and simplify its orchestration:

- Keep the existing component-per-file structure and shared contracts.
- Keep the native KiCad model and portable component snapshot as a coherent,
  validated input bundle to CAD.
- Run PCB review before CAD in one CI job and the same workspace. Retain
  separate PCB and CAD artifacts, uploading only successfully generated output.
- Reuse the reviewed PCB bundle; standalone CAD refreshes it only if missing,
  stale or damaged. PCB failure prevents Blender execution and preserves
  previously published CAD output.
- Remove the unnecessary callback wrapper around CAD's export preparation.
- Correct documentation that overstates the current PCB ownership boundary.

Moving all off-board geometry into PCB or deleting the shared catalog is outside
this smaller change. Off-board geometry builders are not duplicates of the
main-PCB meshes; retain them until a concrete simplification justifies moving
individual parts. Do not add a new assembly schema solely to relocate them.

## Verification

Exercise checked-export reuse, missing/stale/damaged export refresh, interrupted
bundle copying and PCB failure before Blender. Run focused CAD checks and the
full local PCB-to-CAD generation sequence. Verify native DRC, component import
coverage, CAD fit checks and artifact provenance. Inspect regenerated assembly
renders. Validate CI workflow syntax and step order locally; GitHub scheduling
and execution require an actual workflow run.

All changes remain unstaged. Automated fit checks do not establish physical
manufacturing validation.
