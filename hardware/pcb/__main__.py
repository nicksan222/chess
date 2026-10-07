"""Command-line entry for the composed board and harness-based generation."""

import argparse

from pcb.board.board import Board
from pcb.board.generate import generate
from pcb.harness.checks.run import check


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "check", "review", "release"))

    class Options(argparse.Namespace):
        command: str = ""

    args = parser.parse_args(namespace=Options())
    if args.command == "release":
        parser.exit(
            1,
            "Fabrication release is unavailable: manufacturing reassessment, electrical checks and physical evidence are pending.\n",
        )
    if args.command in ("check", "review"):
        check(Board(), electrical=args.command == "check")
    if args.command in ("generate", "review"):
        print(generate())


if __name__ == "__main__":
    main()
