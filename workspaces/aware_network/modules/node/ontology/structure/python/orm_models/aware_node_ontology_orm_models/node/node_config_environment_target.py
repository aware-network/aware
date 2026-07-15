from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_config import EnvironmentConfig
    from aware_node_ontology_orm_models.node.node_config_environment_profile_mount import (
        NodeConfigEnvironmentProfileMount,
    )


class NodeConfigEnvironmentTarget(ORMModel):
    # Relationships
    environment_config: EnvironmentConfig | None = Field(default=None)
    profile_mounts: list[NodeConfigEnvironmentProfileMount] = Field(default_factory=list)

    # Attributes
    environment_handle: str

    # Foreign Keys
    node_config_id: UUID = Field(description="Foreign key for NodeConfig.environment_targets")
    environment_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigEnvironmentTarget.environment_config"
    )
