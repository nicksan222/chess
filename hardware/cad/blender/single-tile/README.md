# Universal single tile

The single tile is split into independent generated elements and import-only
presentation views:

- `top/generate.py` is the sole owner of printable `Tile_Top_Lid` geometry.
- `bottom/generate.py` is the sole owner of printable `Tile_Bottom_Tray` geometry.
- `merged/generate.py` imports those exact `.blend` outputs and owns merged, open,
  and wired views. It creates no printable geometry.

Generic mesh, boolean, scene, studio, and library-loading operations come from
`../modeling.py` and `../presentation.py`. Wired electronics come from the
shared `../tile_electronics.py` reference builder. Board assembly imports the
same generated lid and tray libraries directly.

The tray provides four Velcro placement pockets and two reinforced optional
screw holes. The lid provides the locating rail, hidden magnet-ring recess, and
5050 LED pocket/aperture. The wired view adds a WS2812B-compatible LED carrier,
decoupling capacitor, central reed sensor, and tidy cable harnesses as
non-printable references.

The LED envelope follows the Worldsemi mechanical drawing (nominal
5.0 x 5.4 x 1.57 mm with 0.05 mm default tolerance), cross-checked against
Adafruit's 5 mm package description:

- <https://www.ledyilighting.com/wp-content/uploads/2025/02/WS2812B-datasheet.pdf>
- <https://www.adafruit.com/product/1655>

Run `make regen-all` from the repository root. Generation order is lid, tray,
merged single-tile views, empty board, then full board assembly.
