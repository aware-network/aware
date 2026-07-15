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
    from aware_attention_ontology.session.attention_layout_topology_transition_section import (
        AttentionLayoutTopologyTransitionSection,
    )


class AttentionLayoutTopologyTransition(ORMModel):
    """
    Immutable active-membership transition under one AttentionSessionLayout.
    Contract:
    - One transition is the atomic authority for the complete ordered set of
    active AttentionSessionSection anchors.
    - The active pointer lives on AttentionSessionLayout; history is immutable.
    - Omitted anchors are inactive for this revision, not deleted.
    """

    # Relationships
    previous_topology_transition: AttentionLayoutTopologyTransition | None = Field(default=None)
    section_states: list[AttentionLayoutTopologyTransitionSection] = Field(default_factory=list)

    # Attributes
    client_intent_id: str
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="topology")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.topology_transitions")
    previous_topology_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionLayoutTopologyTransition.previous_topology_transition"
    )

    async def attach_section_state(
        self, attention_session_section_id: UUID, order: int
    ) -> AttentionLayoutTopologyTransitionSection:
        """
        Construct one typed membership row through its immutable parent.

        The public atomic boundary remains
        AttentionSessionLayout.apply_topology_transition.
        """

        payload = {"attention_session_section_id": attention_session_section_id, "order": order}
        result = await invoke_instance(orm_model=self, function_name="attach_section_state", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_layout_topology_transition_section import (
            AttentionLayoutTopologyTransitionSection,
        )

        if isinstance(value, AttentionLayoutTopologyTransitionSection):
            return value
        return AttentionLayoutTopologyTransitionSection.validate_invocation_value(value)

    @classmethod
    async def create_via_attention_session_layout(
        cls,
        attention_session_layout_id: UUID,
        client_intent_id: str,
        previous_topology_transition_id: UUID | None = None,
        sequence: int = 0,
        transition_kind: str = "topology",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> AttentionLayoutTopologyTransition:
        """
        Create one immutable layout-topology transition header.

        The owning AttentionSessionLayout plus client_intent_id provide stable
        replay identity. Section-state rows are constructed only after the
        parent handler validates the complete topology vector.
        """

        payload = {
            "attention_session_layout_id": attention_session_layout_id,
            "client_intent_id": client_intent_id,
            "previous_topology_transition_id": previous_topology_transition_id,
            "sequence": sequence,
            "transition_kind": transition_kind,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_attention_session_layout", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionLayoutTopologyTransition):
            return value
        return AttentionLayoutTopologyTransition.validate_invocation_value(value)


class AttentionLayoutTopologyTransitionAttachSectionStateInput(BaseModel):
    attention_session_section_id: UUID
    order: int


class AttentionLayoutTopologyTransitionAttachSectionStateOutput(BaseModel):
    value: AttentionLayoutTopologyTransitionSection


class AttentionLayoutTopologyTransitionCreateViaAttentionSessionLayoutInput(BaseModel):
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.topology_transitions")
    client_intent_id: str
    previous_topology_transition_id: UUID | None = Field(default=None)
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="topology")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class AttentionLayoutTopologyTransitionCreateViaAttentionSessionLayoutOutput(BaseModel):
    value: AttentionLayoutTopologyTransition


FUNCTIONS = {
    "AttentionLayoutTopologyTransition": {
        "attach_section_state": {
            "canonical": {
                "name": "attach_section_state",
                "description": "Construct one typed membership row through its immutable parent.\n\nThe public atomic boundary remains\nAttentionSessionLayout.apply_topology_transition.",
                "is_constructor": False,
            },
            "input": AttentionLayoutTopologyTransitionAttachSectionStateInput,
            "output": AttentionLayoutTopologyTransitionAttachSectionStateOutput,
        },
        "create_via_attention_session_layout": {
            "canonical": {
                "name": "create_via_attention_session_layout",
                "description": "Create one immutable layout-topology transition header.\n\nThe owning AttentionSessionLayout plus client_intent_id provide stable\nreplay identity. Section-state rows are constructed only after the\nparent handler validates the complete topology vector.",
                "is_constructor": True,
            },
            "input": AttentionLayoutTopologyTransitionCreateViaAttentionSessionLayoutInput,
            "output": AttentionLayoutTopologyTransitionCreateViaAttentionSessionLayoutOutput,
        },
    },
}

__all__ = [
    "AttentionLayoutTopologyTransition",
    "AttentionLayoutTopologyTransitionAttachSectionStateInput",
    "AttentionLayoutTopologyTransitionAttachSectionStateOutput",
    "AttentionLayoutTopologyTransitionCreateViaAttentionSessionLayoutInput",
    "AttentionLayoutTopologyTransitionCreateViaAttentionSessionLayoutOutput",
    "FUNCTIONS",
]
