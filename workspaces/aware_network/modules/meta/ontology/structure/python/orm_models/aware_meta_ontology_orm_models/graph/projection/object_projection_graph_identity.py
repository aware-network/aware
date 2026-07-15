from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_observable import (
        ObjectProjectionGraphObservable,
    )


class ObjectProjectionGraphIdentity(ORMModel):
    """
    Stable identity for a family of ObjectProjectionGraphs under an ObjectConfigGraphIdentity.
    This object is intended to be created by the compiler (environment-artifacts)
    and remain stable even as projection snapshots evolve.
    """

    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None, exclude=True)
    object_instance_graph_identities: list[ObjectInstanceGraphIdentity] = Field(default_factory=list)
    object_projection_graph_observables: list[ObjectProjectionGraphObservable] = Field(default_factory=list)

    # Attributes
    projection_name: str
    label: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)

    # Foreign Keys
    object_config_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphIdentity.object_projection_graph_identities"
    )
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphIdentity.object_projection_graph"
    )
