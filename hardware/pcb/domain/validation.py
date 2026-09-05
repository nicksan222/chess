"""Reusable runtime narrowing at serialized-data boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeGuard


def is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    """Narrow an object decoded from a JSON object.

    JSON object keys are strings by specification; callers separately validate
    every domain value before use.
    """
    return isinstance(value, Mapping)
