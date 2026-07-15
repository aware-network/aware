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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology.layout.layout_section import LayoutSection
    from aware_attention_ontology.section.section import Section
    from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition


class AttentionSessionSection(ORMModel):
    """
    Session-local section state for Attention focus transitions.
    Contract:
    - Parent constructor is AttentionSessionLayout.
    - This row grounds transition history by LayoutSection -> Section.
    - Section.active_focus_scope remains legacy/global current state; replayable
    session focus truth is the transition list under this row.
    """

    # Relationships
    layout_section: LayoutSection | None = Field(default=None)
    section: Section | None = Field(default=None)
    transitions: list[AttentionFocusTransition] = Field(default_factory=list)
    active_transition: AttentionFocusTransition | None = Field(default=None)

    # Attributes
    section_key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)

    # Foreign Keys
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.sections")
    layout_section_id: UUID = Field(description="Foreign key for AttentionSessionSection.layout_section")
    section_id: UUID = Field(description="Foreign key for AttentionSessionSection.section")
    active_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionSection.active_transition"
    )

    async def append_transition(
        self,
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
        Append one replayable focus transition under this session section.

        Contract:
        - This is source truth for replay.
        - It is not an all-in-one read snapshot.
        - Consumers may later derive read DTOs from this row plus session
          layout/section state.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="append_transition", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition

        if isinstance(value, AttentionFocusTransition):
            return value
        return AttentionFocusTransition.validate_invocation_value(value)

    async def set_active_transition(self, attention_focus_transition_id: UUID) -> AttentionFocusTransition:
        """Select the active transition for this session-local section."""

        payload = {"attention_focus_transition_id": attention_focus_transition_id}
        result = await invoke_instance(orm_model=self, function_name="set_active_transition", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition

        if isinstance(value, AttentionFocusTransition):
            return value
        return AttentionFocusTransition.validate_invocation_value(value)

    @classmethod
    async def create_via_attention_session_layout(
        cls,
        attention_session_layout_id: UUID,
        layout_section_id: UUID,
        section_id: UUID,
        section_key: str | None = None,
        order: int = 0,
        is_active: bool = True,
    ) -> AttentionSessionSection:
        """Create one session-local section state row."""

        payload = {
            "attention_session_layout_id": attention_session_layout_id,
            "layout_section_id": layout_section_id,
            "section_id": section_id,
            "section_key": section_key,
            "order": order,
            "is_active": is_active,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_attention_session_layout", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionSessionSection):
            return value
        return AttentionSessionSection.validate_invocation_value(value)


class AttentionSessionSectionAppendTransitionInput(BaseModel):
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


class AttentionSessionSectionAppendTransitionOutput(BaseModel):
    value: AttentionFocusTransition


class AttentionSessionSectionSetActiveTransitionInput(BaseModel):
    attention_focus_transition_id: UUID


class AttentionSessionSectionSetActiveTransitionOutput(BaseModel):
    value: AttentionFocusTransition


class AttentionSessionSectionCreateViaAttentionSessionLayoutInput(BaseModel):
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.sections")
    layout_section_id: UUID
    section_id: UUID
    section_key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class AttentionSessionSectionCreateViaAttentionSessionLayoutOutput(BaseModel):
    value: AttentionSessionSection


FUNCTIONS = {
    "AttentionSessionSection": {
        "append_transition": {
            "canonical": {
                "name": "append_transition",
                "description": "Append one replayable focus transition under this session section.\n\nContract:\n- This is source truth for replay.\n- It is not an all-in-one read snapshot.\n- Consumers may later derive read DTOs from this row plus session\n  layout/section state.",
                "is_constructor": False,
            },
            "input": AttentionSessionSectionAppendTransitionInput,
            "output": AttentionSessionSectionAppendTransitionOutput,
        },
        "set_active_transition": {
            "canonical": {
                "name": "set_active_transition",
                "description": "Select the active transition for this session-local section.",
                "is_constructor": False,
            },
            "input": AttentionSessionSectionSetActiveTransitionInput,
            "output": AttentionSessionSectionSetActiveTransitionOutput,
        },
        "create_via_attention_session_layout": {
            "canonical": {
                "name": "create_via_attention_session_layout",
                "description": "Create one session-local section state row.",
                "is_constructor": True,
            },
            "input": AttentionSessionSectionCreateViaAttentionSessionLayoutInput,
            "output": AttentionSessionSectionCreateViaAttentionSessionLayoutOutput,
        },
    },
}

__all__ = [
    "AttentionSessionSection",
    "AttentionSessionSectionAppendTransitionInput",
    "AttentionSessionSectionAppendTransitionOutput",
    "AttentionSessionSectionSetActiveTransitionInput",
    "AttentionSessionSectionSetActiveTransitionOutput",
    "AttentionSessionSectionCreateViaAttentionSessionLayoutInput",
    "AttentionSessionSectionCreateViaAttentionSessionLayoutOutput",
    "FUNCTIONS",
]
