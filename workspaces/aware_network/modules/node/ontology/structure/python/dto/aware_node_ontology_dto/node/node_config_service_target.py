from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_node_ontology_dto.node.node_config_service_code_package import NodeConfigServiceCodePackage
    from aware_service_ontology_dto.service.service_config import ServiceConfig


class NodeConfigServiceTarget(BaseModel):
    # Relationships
    service_config: ServiceConfig | None = Field(default=None)
    code_packages: list[NodeConfigServiceCodePackage] = Field(default_factory=list)

    # Attributes
    service_name: str
