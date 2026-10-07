"""FDM guardrails and build-volume checks for printed parts."""

from math import isclose

from .case import CASE_OUTER_SIZE_MM
from .panel import (
    PANEL_BUTTON_CAP_BOTTOM_Z_MM,
    PANEL_BUTTON_CAP_SIZE_MM,
    PANEL_OLED_BEZEL_TOP_Z_MM,
    PANEL_OLED_LEDGE_BOTTOM_Z_MM,
)
from .tile_plate import TILE_PLATE_SIZE_MM

# Prototype FDM guardrails. These catch implausible geometry, but do not replace
# printer-, material-, and orientation-specific slicer validation.
#
# Both parts are larger than a desktop printer bed, so they are quoted from an
# FDM print service. The desktop figure is kept to document that fact rather than
# to gate anything: a 404 mm case does not fit a 256 mm bed and never will.
REFERENCE_DESKTOP_BUILD_VOLUME_MM = (256.0, 256.0, 256.0)
REFERENCE_SERVICE_BUILD_VOLUME_MM = (420.0, 420.0, 420.0)
PRINT_BED_EDGE_MARGIN_MM = 5.0
FDM_REFERENCE_NOZZLE_MM = 0.4
FDM_MIN_FEATURE_MM = 2.0 * FDM_REFERENCE_NOZZLE_MM
FDM_MIN_FLOOR_MM = 1.0
FDM_MIN_FIT_CLEARANCE_MM = 0.2
FDM_MAX_FIT_CLEARANCE_MM = 0.5

# Boolean robustness. Cutters overhang the surface they break so coplanar faces
# never meet, which is what keeps the exact solver from leaving holes.
BOOLEAN_RECESS_OVERLAP_MM = 0.2
BOOLEAN_THROUGH_OVERLAP_MM = 0.4

PRINTED_PART_SIZES_MM = (
    CASE_OUTER_SIZE_MM,
    (*TILE_PLATE_SIZE_MM[:2], PANEL_OLED_BEZEL_TOP_Z_MM - PANEL_OLED_LEDGE_BOTTOM_Z_MM),
    PANEL_BUTTON_CAP_SIZE_MM,
)
LONGEST_PRINTED_PART_MM = max(max(part) for part in PRINTED_PART_SIZES_MM)
BOARD_ASSEMBLED_ENVELOPE_MM = (
    *CASE_OUTER_SIZE_MM[:2],
    max(
        CASE_OUTER_SIZE_MM[2],
        PANEL_BUTTON_CAP_BOTTOM_Z_MM + PANEL_BUTTON_CAP_SIZE_MM[2],
    ),
)


def meets(value: float, minimum: float) -> bool:
    """Floating-point safe "value is at least minimum".

    Derived dimensions are sums and differences of decimals, so an exact
    comparison rejects geometry that is on the limit by one part in 10^16.
    """
    return value > minimum or isclose(value, minimum, abs_tol=1e-9)


def usable_build_volume(
    build_volume_mm: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Return the build volume after reserving an edge margin on every side."""
    return (
        build_volume_mm[0] - 2.0 * PRINT_BED_EDGE_MARGIN_MM,
        build_volume_mm[1] - 2.0 * PRINT_BED_EDGE_MARGIN_MM,
        build_volume_mm[2] - 2.0 * PRINT_BED_EDGE_MARGIN_MM,
    )


def fits_build_volume(
    part_dimensions_mm: tuple[float, float, float],
    build_volume_mm: tuple[float, float, float],
) -> bool:
    """Check whether an axis-aligned part fits after rotation and bed margins."""
    part = sorted(part_dimensions_mm)
    usable = sorted(usable_build_volume(build_volume_mm))
    return all(part_axis <= bed_axis for part_axis, bed_axis in zip(part, usable))
