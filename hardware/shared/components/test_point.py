"""Approved product: Harwin S1751-46R SMD test point."""

from .spec import part

# Harwin SMT Hardware p260: S1751-46R is 3.25 x 1.65 x 2.00 mm.
TEST_POINT = part(
    "TEST_POINT",
    "2.0 mm high surface-mount test point",
    "SMD test point",
    "Harwin",
    "S1751-46R",
    (3.25, 1.65, 2.0),
    "https://cdn.harwin.com/pdfs/S1751R.pdf",
)
