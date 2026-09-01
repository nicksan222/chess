# PCBWay fabrication specification — revision C prototype

Use this specification together with the release-generated Gerber and Excellon
files. Do not substitute a different layer count or finished thickness.

| Item | Requirement |
|---|---|
| Board size | 320 x 360 mm |
| Layers | 8 |
| Finished thickness | 1.6 mm |
| Outer copper | 1 oz minimum |
| Inner copper | 1 oz minimum |
| Material | FR-4, Tg 150 °C or higher |
| Surface finish | Lead-free HASL (lowest-cost prototype option) |
| Solder mask | Green, both sides |
| Silkscreen | White, both sides where supplied |
| Minimum design trace/space | 0.31 / 0.30 mm |
| Standard finished via | 0.40 mm drill in 0.90 mm pad |
| Plated component slots | 1.00 x 1.60 mm for J3, three places |
| NPTH mounting holes | 3.40 mm, twenty places |
| Controlled impedance | Not required |
| Edge connector / castellations | None |

## Layer order

1. F.Cu — components and local signals
2. In1.Cu — continuous GND plane
3. In2.Cu — +5 V plane
4. In3.Cu — +3.3 V plane
5. In4.Cu — signals
6. In5.Cu — signals
7. In6.Cu — signals
8. B.Cu — signals

PCBWay may select its standard symmetric 1.6 mm eight-layer dielectric stack
because this board has no controlled-impedance nets. Before payment, obtain the
actual proposed stack-up and confirm 1 oz inner planes, 1.6 mm finished
thickness, and that 0.40 mm through-vias and the three plated slots are accepted.
The large 320 x 360 mm outline should also be confirmed as a single board rather
than automatically panelized.

The order archive must contain all eight copper Gerbers, both masks, both
silkscreens, Edge.Cuts, the Gerber job file, plated drill output, and NPTH drill
output. `./tools/pcb` is the only supported exporter.
