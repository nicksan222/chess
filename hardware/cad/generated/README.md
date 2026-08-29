# Generated CAD artefacts

Build output. Do not edit anything here by hand; rerun the build instead:

```sh
./tools/cad build
```

Every project writes `<project>.blend` plus one PNG per view, named
`<project>.png` or `<project>-<view>.png`. `./tools/cad build` clears this
folder first, so a removed project cannot leave a stale model behind.
