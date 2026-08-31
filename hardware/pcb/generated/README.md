# Generated fabrication artefacts

Build output. Do not edit anything here by hand; rerun the tool instead:

```sh
./tools/pcb
```

What you will find:

- `gerber/` — the layer stack as individual RS-274X files plus an Excellon drill
  file, named the way KiCad names them, which is what most fabs expect.
- `board-top.svg`, `board-bottom.svg` — previews of each side. Open these in a
  browser: they use SVG filters to colour the layers, and many command-line
  rasterisers ignore filters and render the traces white on white.
- `routing.md` — what is connected and what is not. Read this first.
- `board-pcbway.zip` — the upload package. **It only appears when every
  connection in the schematic is realised in copper.** If it is missing,
  `routing.md` says what is outstanding.

That gate exists because a fab cannot tell an unrouted board from a finished one.
Gerber output is valid long before a board would work, so the package is withheld
rather than left for someone to upload by mistake.
