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
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology_orm_models.ontology.ontology_config import OntologyConfig


class EnvironmentConfigOntologyConfig(ORMModel):
    # Relationships
    ontology_config: OntologyConfig | None = Field(default=None)
    ontology_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    environment_config: EnvironmentConfig | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentConfig.ontology_configs"
    )

    # Attributes
    fqn_prefix: str
    name: str

    # Foreign Keys
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.ontology_configs")
    ontology_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentConfigOntologyConfig.ontology_config"
    )
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentConfigOntologyConfig.ontology_config_object_instance_graph_commit",
    )
