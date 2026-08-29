# Generated electronics artefacts

Build output. Do not edit anything here by hand; rerun the build instead:

```sh
./tools/electronics build
```

Every project writes `<project>.svg` and `<project>.png`, and the symbols
placed across all of them are counted into `bom.md`. `./tools/electronics
build` clears this folder first, so a removed project cannot leave a stale
drawing behind.
