from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_identity import (
        ObjectProjectionGraphIdentity,
    )


class Focus(ORMModel):
    """Focus Object. Attention abstraction that allows an Object to be represented at an Interface."""

    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)
    object_projection_graph_identity: ObjectProjectionGraphIdentity | None = Field(default=None, exclude=True)

    # Attributes
    focus_scope_id: UUID
    projection_hash: str | None = Field(default=None)
    target_id: UUID | None = Field(default=None)
    target_type: str | None = Field(default=None)
    description: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)

    # Foreign Keys
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for Focus.object_instance_graph_branch"
    )
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for Focus.object_projection_graph_identity"
    )
