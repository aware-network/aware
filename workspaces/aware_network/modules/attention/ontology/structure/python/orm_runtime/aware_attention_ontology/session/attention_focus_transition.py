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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology.focus.focus import Focus
    from aware_attention_ontology.focus.focus_scope import FocusScope
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_meta_ontology.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity
    from aware_meta_ontology.graph.projection.object_projection_graph_observable import ObjectProjectionGraphObservable


class AttentionFocusTransition(ORMModel):
    """
    Replayable Attention focus transition under one AttentionSessionSection.
    Contract:
    - This is the ontology source event for session replay.
    - It is grounded by parent AttentionSessionSection, which is grounded by
    AttentionSessionLayout and AttentionSession.
    - It records focus/observable/graph coordinates, not a consumer snapshot.
    """

    # Relationships
    previous_transition: AttentionFocusTransition | None = Field(default=None)
    focus_scope: FocusScope | None = Field(default=None)
    focus: Focus | None = Field(default=None)
    observable: ObjectProjectionGraphObservable | None = Field(default=None)
    object_projection_graph_identity: ObjectProjectionGraphIdentity | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    transition_key: str
    sequence: int = Field(default=0)
    projection_hash: str | None = Field(default=None)
    transition_kind: str = Field(default="focus")
    rationale: str | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    attention_session_section_id: UUID = Field(description="Foreign key for AttentionSessionSection.transitions")
    previous_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.previous_transition"
    )
    focus_scope_id: UUID = Field(description="Foreign key for AttentionFocusTransition.focus_scope")
    focus_id: UUID | None = Field(default=None, description="Foreign key for AttentionFocusTransition.focus")
    observable_id: UUID | None = Field(default=None, description="Foreign key for AttentionFocusTransition.observable")
    object_projection_graph_identity_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.object_projection_graph_identity"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.object_instance_graph_branch"
    )
    object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionFocusTransition.object_instance_graph_commit"
    )

    @classmethod
    async def create_via_attention_session_section(
        cls,
        attention_session_section_id: UUID,
        transition_key: str,
        focus_scope_id: UUID,
        focus_id: UUID | None = None,
        observable_id: UUID | None = None,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        object_instance_graph_commit_id: UUID | None = None,
        previous_transition_id: UUID | None = None,
        sequence: int = 0,
        projection_hash: str | None = None,
        transition_kind: str = "focus",
        rationale: str | None = None,
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> AttentionFocusTransition:
        """
        Create one focus transition under an AttentionSessionSection.

        Contract:
        - Parent section scope and transition key provide stable replay identity.
        - FocusScope is required because every transition must resolve the
          session-local focus scope.
        - Other focus/observable/graph links are optional to allow partial
          transitions such as section activation before graph commit evidence is
          available.
        """

        payload = {
            "attention_session_section_id": attention_session_section_id,
            "transition_key": transition_key,
            "focus_scope_id": focus_scope_id,
            "focus_id": focus_id,
            "observable_id": observable_id,
            "object_projection_graph_identity_id": object_projection_graph_identity_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "previous_transition_id": previous_transition_id,
            "sequence": sequence,
            "projection_hash": projection_hash,
            "transition_kind": transition_kind,
            "rationale": rationale,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_attention_session_section", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionFocusTransition):
            return value
        return AttentionFocusTransition.validate_invocation_value(value)


class AttentionFocusTransitionCreateViaAttentionSessionSectionInput(BaseModel):
    attention_session_section_id: UUID = Field(description="Foreign key for AttentionSessionSection.transitions")
    transition_key: str
    focus_scope_id: UUID
    focus_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    previous_transition_id: UUID | None = Field(default=None)
    sequence: int = Field(default=0)
    projection_hash: str | None = Field(default=None)
    transition_kind: str = Field(default="focus")
    rationale: str | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class AttentionFocusTransitionCreateViaAttentionSessionSectionOutput(BaseModel):
    value: AttentionFocusTransition


FUNCTIONS = {
    "AttentionFocusTransition": {
        "create_via_attention_session_section": {
            "canonical": {
                "name": "create_via_attention_session_section",
                "description": "Create one focus transition under an AttentionSessionSection.\n\nContract:\n- Parent section scope and transition key provide stable replay identity.\n- FocusScope is required because every transition must resolve the\n  session-local focus scope.\n- Other focus/observable/graph links are optional to allow partial\n  transitions such as section activation before graph commit evidence is\n  available.",
                "is_constructor": True,
            },
            "input": AttentionFocusTransitionCreateViaAttentionSessionSectionInput,
            "output": AttentionFocusTransitionCreateViaAttentionSessionSectionOutput,
        },
    },
}

__all__ = [
    "AttentionFocusTransition",
    "AttentionFocusTransitionCreateViaAttentionSessionSectionInput",
    "AttentionFocusTransitionCreateViaAttentionSessionSectionOutput",
    "FUNCTIONS",
]
