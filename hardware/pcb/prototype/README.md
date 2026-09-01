# Hall-sensor and magnet prototype

Fabrication requires measurements from one DRV5032FCDBZR with its local bypass
capacitor, one SK9822, and one MCP23017 at the final CAD stack height. Test the
actual production chess-piece magnet with both poles facing the sensor.

Create `hall-magnet.json` only from physical measurements:

```json
{
  "schema": 1,
  "board_revision": "C-PROTOTYPE",
  "sensor_mpn": "DRV5032FCDBZR",
  "final_gap_mm": 4.2,
  "north": {
    "operate_mm": [6.1, 6.0, 6.2, 6.1, 6.0],
    "release_mm": [7.0, 6.9, 7.1, 7.0, 6.9]
  },
  "south": {
    "operate_mm": [6.0, 5.9, 6.1, 6.0, 5.9],
    "release_mm": [6.8, 6.7, 6.9, 6.8, 6.7]
  },
  "pass": true,
  "notes": "Magnet MPN, fixture, temperature, instruments, and observations."
}
```

The numbers above only illustrate the schema; do not copy them as evidence. The
release gate requires at least five operate and five release measurements per
pole, plus at least 0.5 mm operate-distance margin beyond the final measured gap.
