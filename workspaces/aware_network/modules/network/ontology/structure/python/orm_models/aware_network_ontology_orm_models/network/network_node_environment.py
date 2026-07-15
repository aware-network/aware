from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology Orm Models
from aware_network_ontology_orm_models.network.network_enums import NetworkEnvironmentRole

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment import Environment


class NetworkNodeEnvironment(ORMModel):
    # Relationships
    environment: Environment | None = Field(default=None, exclude=True)

    # Attributes
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)
    role: NetworkEnvironmentRole = Field(default=NetworkEnvironmentRole.replica)

    # Foreign Keys
    network_node_id: UUID = Field(description="Foreign key for NetworkNode.environments")
    environment_id: UUID = Field(description="Foreign key for NetworkNodeEnvironment.environment")
