"""Validated identity and body envelope for one approved product.

Role: the single record of what may be purchased/placed. `ComponentSpec` holds the
exact manufacturer part number (MPN), package label, nominal body size and datasheet
link; PCB parts and the BOM look products up by `key` (CAD takes bodies via
`shared/dimensions`) instead of
copying these facts. A render or a clean DRC never authorizes substituting a part:
changing a product means editing its file here and re-validating footprints.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentSpec:
    """Approved-part identity and nominal manufacturer L/W/H envelope."""

    key: str  # Stable internal identifier, e.g. "HALL_SENSOR"; never an MPN.
    description: str
    package: str  # Label that the PCB footprint's Package field must equal.
    manufacturer: str
    mpn: str
    body_mm: tuple[float, float, float] | None = None  # Nominal L x W x H, mm.
    datasheet: str = ""
    # Bought by the piece unless this names a bulk unit (e.g. a wire spool); then
    # one kit takes `cut_length_mm` of it per BOM count.
    purchase_unit: str = "each"
    cut_length_mm: float | None = None

    def __post_init__(self) -> None:
        """Keep invalid purchasing and envelope data out of every domain."""
        for field_name in ("key", "description", "package", "manufacturer", "mpn"):
            if not getattr(self, field_name):
                raise ValueError(f"component {field_name} must not be empty")
        if self.body_mm is not None and any(axis <= 0.0 for axis in self.body_mm):
            raise ValueError(f"{self.key}: body dimensions must be positive")
        if self.cut_length_mm is not None and self.cut_length_mm <= 0.0:
            raise ValueError(f"{self.key}: cut length must be positive")

    def kit_quantity(self, count: int) -> str:
        """What one board's kit takes: pieces, or pieces cut to length."""
        if self.cut_length_mm is None:
            return str(count)
        return f"{count} x {self.cut_length_mm:g} mm"

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
    *,
    purchase_unit: str = "each",
    cut_length_mm: float | None = None,
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
        purchase_unit,
        cut_length_mm,
    )
