"""Consumer interface for the original admitted joint host, not its authentication."""
from typing import Protocol


class CatalogJointHost(Protocol):
    def validate_catalog_parent(self) -> None:
        """Validate original parent/process/transaction; raise unless live.

        The sole joint host implements this from retained original authority.
        Implementing this Protocol or returning successfully grants no authority.
        """
        ...

    def catalogs_published(self) -> bool:
        """True only after synchronized paired publication, false after closure.

        No source I/O or semantic execution here. The original owner must prevent
        publication before both prepared legs and final source/lifetime checks.
        """
        ...
