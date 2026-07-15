from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.render_component_package import RenderComponentPackage


class InterfacePackageRenderComponentPackage(ORMModel):
    # Relationships
    render_component_package: RenderComponentPackage

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.render_component_packages")
    render_component_package_id: UUID | None = Field(
        default=None, description="Foreign key for InterfacePackageRenderComponentPackage.render_component_package"
    )
