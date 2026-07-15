from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_config import EnvironmentConfig
    from aware_node_ontology_dto.node.node_config_environment_profile_mount import NodeConfigEnvironmentProfileMount


class NodeConfigEnvironmentTarget(BaseModel):
    # Relationships
    environment_config: EnvironmentConfig | None = Field(default=None)
    profile_mounts: list[NodeConfigEnvironmentProfileMount] = Field(default_factory=list)

    # Attributes
    environment_handle: str
