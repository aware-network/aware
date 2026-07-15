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

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity


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

    @classmethod
    async def build(
        cls,
        focus_scope_id: UUID,
        object_projection_graph_identity_id: UUID,
        projection_hash: str | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        target_type: str | None = None,
        target_id: UUID | None = None,
        description: str | None = None,
        expires_at: datetime | None = None,
        is_active: bool = True,
        last_accessed: datetime | None = None,
    ) -> Focus:
        """Builds a new Focus."""

        payload = {
            "focus_scope_id": focus_scope_id,
            "object_projection_graph_identity_id": object_projection_graph_identity_id,
            "projection_hash": projection_hash,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "target_type": target_type,
            "target_id": target_id,
            "description": description,
            "expires_at": expires_at,
            "is_active": is_active,
            "last_accessed": last_accessed,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Focus):
            return value
        return Focus.validate_invocation_value(value)


class FocusBuildInput(BaseModel):
    focus_scope_id: UUID
    object_projection_graph_identity_id: UUID
    projection_hash: str | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    target_type: str | None = Field(default=None)
    target_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)


class FocusBuildOutput(BaseModel):
    value: Focus


FUNCTIONS = {
    "Focus": {
        "build": {
            "canonical": {"name": "build", "description": "Builds a new Focus.", "is_constructor": True},
            "input": FocusBuildInput,
            "output": FocusBuildOutput,
        },
    },
}

__all__ = [
    "Focus",
    "FocusBuildInput",
    "FocusBuildOutput",
    "FUNCTIONS",
]
