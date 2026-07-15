from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity


class Focus(BaseModel):
    """Focus Object. Attention abstraction that allows an Object to be represented at an Interface."""

    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    object_projection_graph_identity: ObjectProjectionGraphIdentity | None = Field(default=None)

    # Attributes
    focus_scope_id: UUID
    projection_hash: str | None = Field(default=None)
    target_id: UUID | None = Field(default=None)
    target_type: str | None = Field(default=None)
    description: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)
