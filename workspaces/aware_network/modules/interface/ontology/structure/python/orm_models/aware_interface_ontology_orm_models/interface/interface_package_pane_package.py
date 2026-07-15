from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.pane_package import PanePackage


class InterfacePackagePanePackage(ORMModel):
    # Relationships
    pane_package: PanePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.pane_packages")
    pane_package_id: UUID = Field(description="Foreign key for InterfacePackagePanePackage.pane_package")
