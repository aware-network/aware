from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_node_ontology_dto.node.node_package import NodePackage


class NodePackageIncludedNodePackage(BaseModel):
    # Relationships
    included_node_package: NodePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    include_key: str | None = Field(default=None)
    included_package_name: str
