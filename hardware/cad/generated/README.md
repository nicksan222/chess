# Generated CAD artefacts

Build output. Do not edit anything here by hand; rerun the tool instead:

```sh
just --justfile hardware/cad/justfile generate
```

Every project writes `<project>.blend` plus one PNG per view, named
`<project>.png` or `<project>-<view>.png`. The build publishes the complete set
from a sibling staging directory, so failures preserve this directory and a
successful run removes artifacts no longer produced by any project.
