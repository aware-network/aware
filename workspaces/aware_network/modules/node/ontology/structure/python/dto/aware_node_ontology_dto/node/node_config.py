from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_node_ontology_dto.node.node_config_environment_target import NodeConfigEnvironmentTarget
    from aware_node_ontology_dto.node.node_config_interface_target import NodeConfigInterfaceTarget
    from aware_node_ontology_dto.node.node_config_ontology_target import NodeConfigOntologyTarget
    from aware_node_ontology_dto.node.node_config_service_target import NodeConfigServiceTarget


class NodeConfig(BaseModel):
    # Relationships
    environment_targets: list[NodeConfigEnvironmentTarget] = Field(default_factory=list)
    ontology_targets: list[NodeConfigOntologyTarget] = Field(default_factory=list)
    service_targets: list[NodeConfigServiceTarget] = Field(default_factory=list)
    interface_targets: list[NodeConfigInterfaceTarget] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
