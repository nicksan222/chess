"""Publish the schematic's connectivity as a machine-readable artefact.

The fabrication domain needs to know which pins share a net, and which footprint
each reference wants. It should not have to import this domain to find out: doing
so would drag Schemdraw and matplotlib into a toolchain that only needs to write
Gerbers.

So the schematic publishes `netlist.json` and `hardware/pcb` consumes it. The
join is a file, which keeps the two domains independently installable and makes
the contract between them something you can read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ELECTRONICS_ROOT = Path(__file__).resolve().parents[1]
if str(ELECTRONICS_ROOT) not in sys.path:
    sys.path.insert(0, str(ELECTRONICS_ROOT))

from core import bom  # noqa: E402

GENERATED = ELECTRONICS_ROOT / "generated"
OUTPUT = GENERATED / "netlist.json"
GENERATED_BY = "hardware/electronics/core/netlist.py"
SCHEMA_VERSION = 1


def connections(schematic) -> list[dict]:
    """Every electrically joined set of pads, named or not.

    Named nets alone are not enough. A link drawn as a plain wire carries no net
    name, and the LED chain uses them for every step along a rank. Publishing
    only named nets would hide those connections from the fabrication domain,
    which would then happily produce a board with an unrouted LED chain and no
    indication anything was missing.

    So this publishes the schematic's full equivalence classes and attaches a
    name where one exists.
    """
    circuits = schematic.equivalence()
    names = {
        pad: net for net, nodes in schematic.nets().items() for pad in nodes
    }
    grouped: dict[int, set] = {}
    for pad, circuit in circuits.items():
        grouped.setdefault(circuit, set()).add(pad)

    published = []
    for pads in grouped.values():
        labels = {names[pad] for pad in pads if pad in names}
        if len(labels) > 1:
            raise RuntimeError(f"One circuit carries several net names: {labels}")
        published.append(
            {
                "name": next(iter(labels)) if labels else None,
                "pads": sorted([reference, pin] for reference, pin in pads),
            }
        )
    published.sort(key=lambda entry: (entry["name"] or "~", entry["pads"]))
    return published


def document() -> dict:
    """One entry per project, though there is only ever one board."""
    projects = {}
    for name, path in bom.projects():
        info, schematic = bom.assemble(name, path)
        projects[name] = {
            "title": info.title,
            "revision": info.rev,
            "connections": connections(schematic),
            "nets": {
                net: sorted([reference, pin] for reference, pin in nodes)
                for net, nodes in sorted(schematic.nets().items())
            },
            "components": {
                spec.reference: {
                    "lib": spec.lib,
                    "value": spec.value,
                    "package": spec.package,
                    "description": spec.description,
                    "extras": spec.extras,
                }
                for spec in sorted(schematic.symbols, key=lambda s: s.reference)
            },
        }
    return {
        "schema": SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "warning": "Generated file. Do not edit by hand.",
        "projects": projects,
    }


def main() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document(), indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
