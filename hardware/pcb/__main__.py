"""Run with PYTHONPATH=hardware python3 -m pcb."""

from __future__ import annotations

import argparse
from typing import Literal, cast

from pcb import build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "check", "review", "release"))
    args = parser.parse_args()
    command = cast(Literal["generate", "check", "review", "release"], args.command)
    try:
        if command == "check":
            build.check()
        else:
            build.build(command)
    except (RuntimeError, OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
