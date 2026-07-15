from __future__ import annotations

# Standard
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
    from aware_attention_ontology.focus.focus import Focus
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FocusScopeCommit(ORMModel):
    """
    Provenance pin for a Meta OIG commit observed under one FocusScope.
    Contract:
    - Attention owns this context pointer.
    - Meta remains the commit authority through ObjectInstanceGraphCommit.
    - This is not a semantic `Change` object; consumers reconstruct meaning from
    the pinned commit deltas.
    - Observation time is the create commit time of this FocusScopeCommit.
    """

    # Relationships
    focus: Focus | None = Field(default=None)
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Foreign Keys
    focus_scope_id: UUID = Field(description="Foreign key for FocusScope.commits")
    focus_id: UUID = Field(description="Foreign key for FocusScopeCommit.focus")
    object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for FocusScopeCommit.object_instance_graph_commit"
    )

    @classmethod
    async def create_via_focus_scope(
        cls, focus_scope_id: UUID, focus_id: UUID, object_instance_graph_commit_id: UUID
    ) -> FocusScopeCommit:
        """Attach one existing Meta OIG commit under this FocusScope."""

        payload = {
            "focus_scope_id": focus_scope_id,
            "focus_id": focus_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_focus_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FocusScopeCommit):
            return value
        return FocusScopeCommit.validate_invocation_value(value)


class FocusScopeCommitCreateViaFocusScopeInput(BaseModel):
    focus_scope_id: UUID = Field(description="Foreign key for FocusScope.commits")
    focus_id: UUID
    object_instance_graph_commit_id: UUID


class FocusScopeCommitCreateViaFocusScopeOutput(BaseModel):
    value: FocusScopeCommit


FUNCTIONS = {
    "FocusScopeCommit": {
        "create_via_focus_scope": {
            "canonical": {
                "name": "create_via_focus_scope",
                "description": "Attach one existing Meta OIG commit under this FocusScope.",
                "is_constructor": True,
            },
            "input": FocusScopeCommitCreateViaFocusScopeInput,
            "output": FocusScopeCommitCreateViaFocusScopeOutput,
        },
    },
}

__all__ = [
    "FocusScopeCommit",
    "FocusScopeCommitCreateViaFocusScopeInput",
    "FocusScopeCommitCreateViaFocusScopeOutput",
    "FUNCTIONS",
]
