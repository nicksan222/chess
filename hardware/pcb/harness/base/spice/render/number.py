"""Write declared Python numbers to SPICE without silent precision loss."""

from __future__ import annotations


def spice_number(value: float) -> str:
    """Return a numeric literal that round-trips the declared value.

    Python's normal decimal rendering uses enough digits to recover a float
    exactly, while keeping whole-number inputs compact. A six-digit ``:g``
    format can collapse a voltage source or two distinct assertion limits.
    Validation of finite values belongs to the typed declaration classes.
    """
    return str(value)
