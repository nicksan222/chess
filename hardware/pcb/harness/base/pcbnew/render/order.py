"""Put KiCad footprint blocks in a stable order for reviewable output.

KiCad may enumerate board footprints in a different order on successive runs.
Their order in a board file has no electrical meaning, but a changed order
creates a large diff. This module touches only whole, top-level footprint
blocks after KiCad has rendered the board. It leaves their contents, all other
board objects, and the whitespace between blocks unchanged.
"""

from __future__ import annotations

import re

_REFERENCE = re.compile(r'\(property\s+"Reference"\s+"([^"]+)"')


def order_footprints(source: str) -> str:
    """Sort whole footprints by reference in a serialized KiCad board.

    Parentheses within quoted text are ignored while finding block boundaries.
    Missing or repeated references are errors because neither can provide an
    unambiguous component identity. Other board content keeps its exact bytes.
    """
    spans: list[tuple[int, int]] = []
    depth = 0
    quoted = False
    escaped = False
    footprint_start: int | None = None
    for index, char in enumerate(source):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            if (
                depth == 1
                and source.startswith("(footprint", index)
                and source[index + len("(footprint") : index + len("(footprint") + 1]
                in {" ", "\t", "\n", "\r"}
            ):
                footprint_start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced KiCad board text")
            if depth == 1 and footprint_start is not None:
                spans.append((footprint_start, index + 1))
                footprint_start = None
    if depth != 0 or quoted:
        raise ValueError("unbalanced KiCad board text")

    blocks = [source[start:end] for start, end in spans]
    references: list[str] = []
    for block in blocks:
        match = _REFERENCE.search(block)
        if match is None:
            raise ValueError("footprint is missing Reference property")
        references.append(match.group(1))
    if len(references) != len(set(references)):
        raise ValueError("duplicate footprint reference")

    ordered = [
        block for _, block in sorted(zip(references, blocks), key=lambda pair: pair[0])
    ]
    result = source
    for (start, end), block in reversed(list(zip(spans, ordered))):
        result = result[:start] + block + result[end:]
    return result
