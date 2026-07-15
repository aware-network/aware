from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.pane_package import PanePackage


class InterfacePackagePanePackage(BaseModel):
    # Relationships
    pane_package: PanePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
