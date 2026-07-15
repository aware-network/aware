from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_network_ontology_dto.network.network_node_config import NetworkNodeConfig


class NetworkNodePackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    network_node_config: NetworkNodeConfig | None = Field(default=None)

    # Attributes
    name: str
