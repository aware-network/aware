from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology
from aware_network_ontology.network.network_enums import NetworkEnvironmentRole


class NetworkNodeEnvironmentListItem(BaseModel):
    # Attributes
    id: UUID
    environment_id: UUID
    role: NetworkEnvironmentRole
    is_active: bool
    priority: int


class NetworkNodeEnvironmentListResponse(BaseModel):
    # Attributes
    results: list[NetworkNodeEnvironmentListItem] = Field(default_factory=list)
