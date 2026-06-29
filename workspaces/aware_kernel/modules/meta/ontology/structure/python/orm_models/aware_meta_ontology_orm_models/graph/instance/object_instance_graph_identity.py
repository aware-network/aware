from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology_orm_models.class_.class_instance_relationship_identity import (
        ClassInstanceRelationshipIdentity,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ObjectInstanceGraphIdentity(ORMModel):
    """
    Stable identity for a worldline's ObjectInstanceGraph (instance identity).
    IMPORTANT:
    - This is NOT a snapshot graph (no hash, no class instances).
    - Domain commits reference this identity via `object_instance_graph_id`.
    - Snapshots are derived from commits + (OCG, OPG) at materialization time.
    """

    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(default=None, exclude=True)
    class_instance_identities: list[ClassInstanceIdentity] = Field(default_factory=list)
    class_instance_relationship_identities: list[ClassInstanceRelationshipIdentity] = Field(default_factory=list)
    object_instance_graph_changes: list[ObjectInstanceGraphChange] = Field(default_factory=list, exclude=True)
    object_instance_graph_branches: list[ObjectInstanceGraphBranch] = Field(default_factory=list, exclude=True)
    object_instance_graph_commits: list[ObjectInstanceGraphCommit] = Field(default_factory=list, exclude=True)

    # Attributes
    label: str | None = Field(default=None)

    # Foreign Keys
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphIdentity.object_instance_graph_identities"
    )
    object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph"
    )
