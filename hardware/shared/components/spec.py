"""Validated identity and body envelope for one approved product."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentSpec:
    """Approved-part identity and nominal manufacturer L/W/H envelope."""

    key: str
    description: str
    package: str
    manufacturer: str
    mpn: str
    body_mm: tuple[float, float, float] | None = None
    datasheet: str = ""

    def __post_init__(self) -> None:
        """Keep invalid purchasing and envelope data out of every domain."""
        for field_name in ("key", "description", "package", "manufacturer", "mpn"):
            if not getattr(self, field_name):
                raise ValueError(f"component {field_name} must not be empty")
        if self.body_mm is not None and any(axis <= 0.0 for axis in self.body_mm):
            raise ValueError(f"{self.key}: body dimensions must be positive")

    def require_body_mm(self) -> tuple[float, float, float]:
        """Return the body envelope, failing clearly when geometry is unspecified."""
        if self.body_mm is None:
            raise ValueError(f"{self.key} has no body dimensions")
        return self.body_mm


def part(
    key: str,
    description: str,
    package: str,
    manufacturer: str,
    mpn: str,
    body_mm: tuple[float, float, float] | None = None,
    datasheet: str = "",
) -> ComponentSpec:
    """Define one exact, purchasable component."""
    return ComponentSpec(
        key,
        description,
        package,
        manufacturer,
        mpn,
        body_mm,
        datasheet,
    )
