from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import NetworkAppType

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment import Environment
    from aware_network_ontology_dto.network.network_node import NetworkNode


class NetworkOperationHop(BaseModel):
    # Relationships
    source_environment: Environment | None = Field(default=None)
    source_node: NetworkNode | None = Field(default=None)
    target_environment: Environment | None = Field(default=None)
    target_node: NetworkNode | None = Field(default=None)

    # Attributes
    source_interface_id: UUID | None = Field(default=None)
    target_interface_id: UUID | None = Field(default=None)
    hop_index: int
    source_app_type: NetworkAppType
    target_app_type: NetworkAppType
