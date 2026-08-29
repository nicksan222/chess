# Single square

`generate.py` owns only the single-square schematic: one reed cell, column
pull-up, and WS2812B with local decoupling. Other projects reuse
`blocks/square.py`; they do not duplicate that cell.

Net labels (`ROW_n`, `COL_n`, `+5V`, `GND`, `LED_DIN`, `LED_DOUT`) match the
full chessboard so this sheet can compose into later wiring.

Published output is `square.svg` and `square.png` in
`hardware/electronics/generated`.

Run `./tools/electronics` from the repository root.
