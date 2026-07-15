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
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology_dto.ontology.ontology_config import OntologyConfig


class EnvironmentConfigOntologyConfig(BaseModel):
    # Relationships
    ontology_config: OntologyConfig | None = Field(default=None)
    ontology_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    environment_config: EnvironmentConfig | None = Field(
        default=None, description="Reverse view for EnvironmentConfig.ontology_configs"
    )

    # Attributes
    fqn_prefix: str
    name: str
