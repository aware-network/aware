from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology_orm_models.ontology.ontology import Ontology


class OntologyConfig(ORMModel):
    """
    Canonical config/schema root for one ontology.
    `OntologyPackage` remains package/distribution truth and points at
    `ObjectConfigGraphPackage`. `OntologyConfig` is the ontology-owned config
    root that points at the actual `ObjectConfigGraph` schema it configures.
    """

    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None)
    object_config_graph_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    ontologies: list[Ontology] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    fqn_prefix: str
    name: str
    schema_hash: str | None = Field(default=None)
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    object_config_graph_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyConfig.object_config_graph"
    )
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyConfig.object_config_graph_object_instance_graph_commit"
    )
