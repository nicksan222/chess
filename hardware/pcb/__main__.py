"""Run with PYTHONPATH=hardware python3 -m pcb."""

from __future__ import annotations

import argparse

from pcb import build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "check", "review", "release"))
    args = parser.parse_args()
    try:
        if args.command == "check":
            build.check()
        else:
            build.build(args.command)
    except (RuntimeError, OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
