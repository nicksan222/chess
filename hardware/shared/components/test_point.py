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
    "https://content.harwin.com/asset/e4e6a5e1-de35-4a2b-8b49-ff06562cba9d/DRG-02202-Technical-Drawing-Datasheet-S1751R-pdf.pdf",
)
