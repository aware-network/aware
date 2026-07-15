from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_observable import (
        ObjectProjectionGraphObservable,
    )


class ObjectProjectionGraphIdentity(BaseModel):
    """
    Stable identity for a family of ObjectProjectionGraphs under an ObjectConfigGraphIdentity.
    This object is intended to be created by the compiler (environment-artifacts)
    and remain stable even as projection snapshots evolve.
    """

    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)
    object_instance_graph_identities: list[ObjectInstanceGraphIdentity] = Field(default_factory=list)
    object_projection_graph_observables: list[ObjectProjectionGraphObservable] = Field(default_factory=list)

    # Attributes
    projection_name: str
    label: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)
