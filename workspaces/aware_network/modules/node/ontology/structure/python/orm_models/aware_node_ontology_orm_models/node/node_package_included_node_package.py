from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_node_ontology_orm_models.node.node_package import NodePackage


class NodePackageIncludedNodePackage(ORMModel):
    # Relationships
    included_node_package: NodePackage | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    include_key: str | None = Field(default=None)
    included_package_name: str

    # Foreign Keys
    node_package_id: UUID = Field(description="Foreign key for NodePackage.included_node_packages")
    included_node_package_id: UUID = Field(
        description="Foreign key for NodePackageIncludedNodePackage.included_node_package"
    )
