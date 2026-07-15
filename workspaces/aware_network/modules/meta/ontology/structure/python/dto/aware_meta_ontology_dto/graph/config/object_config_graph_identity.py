from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity


class ObjectConfigGraphIdentity(BaseModel):
    """
    Stable identity for a family of ObjectConfigGraphs.
    This object is intended to be created by the compiler (environment-artifacts)
    and remain stable even as config graph snapshots evolve.
    """

    # Relationships
    object_projection_graph_identities: list[ObjectProjectionGraphIdentity] = Field(default_factory=list)

    # Attributes
    key: str = Field(description="Stable key for this config graph family (e.g. fqn_prefix).")
    label: str | None = Field(default=None)
