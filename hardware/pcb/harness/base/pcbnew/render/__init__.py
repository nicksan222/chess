"""Convert declarative board geometry into native KiCad objects."""

# Keep this package importable on systems without KiCad. Circuit.write_board()
# loads the native adapter only when a PCB is actually requested.
