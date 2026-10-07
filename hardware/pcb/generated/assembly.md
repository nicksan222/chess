# Assembly review files

`assembly-bom.csv`: grouped on-board parts, quantities and mounting types.
`assembly-smd.csv`: surface-mount placements; `assembly-through-hole.csv`: through-hole/hybrid placements for separate assembly review.
Native KiCad millimetre XY, rotation and top/bottom conventions are retained; confirm origin, bottom-side orientation and pin 1 with the assembler.
`positions.csv` includes all mounted parts with package/MPN identity.
`harness.md` and `harness-bom.csv`: off-board wire assemblies, separate from the PCB BOM.

These are local review exports. Stackup, electrical roles and physical manufacturing approval remain pending.
