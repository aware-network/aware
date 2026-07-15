from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import NetworkEnvironmentRole

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment import Environment


class NetworkNodeEnvironment(BaseModel):
    # Relationships
    environment: Environment | None = Field(default=None)

    # Attributes
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)
    role: NetworkEnvironmentRole = Field(default=NetworkEnvironmentRole.replica)
