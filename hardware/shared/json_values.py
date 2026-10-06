"""Typed boundary for Python's dynamically typed JSON decoder.

Role: `json.loads` returns `Any`, which the strict type checker (no dynamic types)
rejects. Routing every decode through here confines the one `cast` to this file;
callers then narrow the `object` they get back explicitly.
"""

import json
from typing import cast


def parse_json(text: str | bytes) -> object:
    """Decode JSON without leaking the decoder's dynamic return type."""
    return cast(object, json.loads(text))
