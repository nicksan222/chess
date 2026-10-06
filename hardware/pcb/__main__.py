"""Run with PYTHONPATH=hardware python3 -m pcb.

Role: command-line entry point (`just --justfile hardware/pcb/justfile <recipe>`
wraps it). Maps the four commands to `build.py`: `check` runs only the
non-publishing source checks; `generate`, `review` and `release` publish a full
generated set with increasing amounts of verification. The module docstring doubles
as the argparse description, so keep its first line a usable usage hint.
"""

from __future__ import annotations

import argparse
from typing import Literal, cast

from pcb import build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "check", "review", "release"))
    args = parser.parse_args()
    # argparse already restricted the value; the cast only tells the type checker.
    command = cast(Literal["generate", "check", "review", "release"], args.command)
    try:
        if command == "check":
            build.check()
        else:
            build.build(command)
    # Expected failures (a failed tool, missing file, invalid design) become a
    # one-line message and exit status 1 instead of a traceback.
    except (RuntimeError, OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
