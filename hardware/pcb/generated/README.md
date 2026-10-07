# Generated PCB

Source: `pcb.board.board.Board()`. Regenerate with `PYTHONPATH=hardware python3 -m pcb.board.generate`.

Open `chess-board.kicad_pro` in KiCad. Schematics embed all symbols and show the declared pin maps; PCB footprints come from component land patterns. The exported schematic netlist is checked against every declared connected pin.

The PCB includes routed copper, filled internal rail planes, mounting holes and assembly markings. ERC/DRC findings are in `erc.json` and `drc.json`. Electrical pin roles are unspecified; ERC does not validate driver/power compatibility. `board-top.svg` and `board-top.png` show the same copper view; bottom views are mirrored. `board-connections.svg` shows logical connectivity as dashed airwires, not extra copper. `manifest.json` lists remaining work. The fabrication ZIP contains Gerbers and drill files; generating it does not approve manufacturing.

Board-specific sensing and button simulations passed; results are in `electrical-checks/`. These use ideal sensor, contact and external GPIO bias models; I2C, magnetic margins, firmware debounce and a complete board model remain untested.
