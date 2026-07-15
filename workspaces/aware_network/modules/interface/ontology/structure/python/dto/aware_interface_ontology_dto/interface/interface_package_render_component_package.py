from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.render_component_package import RenderComponentPackage


class InterfacePackageRenderComponentPackage(BaseModel):
    # Relationships
    render_component_package: RenderComponentPackage

    # Attributes
    description: str | None = Field(default=None)
