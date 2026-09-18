"""Typed boundary for Python's dynamically typed JSON decoder."""

import json
from typing import cast


def parse_json(text: str | bytes) -> object:
    """Decode JSON without leaking the decoder's dynamic return type."""
    return cast(object, json.loads(text))
