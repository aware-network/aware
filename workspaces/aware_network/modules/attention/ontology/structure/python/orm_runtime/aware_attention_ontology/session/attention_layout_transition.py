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
    from aware_attention_ontology.session.attention_layout_topology_transition import AttentionLayoutTopologyTransition
    from aware_attention_ontology.session.attention_layout_transition_section import AttentionLayoutTransitionSection


class AttentionLayoutTransition(ORMModel):
    """
    Immutable shared-layout transition under one AttentionSessionLayout.
    Contract:
    - One transition is the atomic authority for a complete mounted-section
    geometry vector.
    - The active pointer lives on AttentionSessionLayout; history is immutable.
    - Renderer pixels and mutable package defaults are not persisted here.
    """

    # Relationships
    previous_transition: AttentionLayoutTransition | None = Field(default=None)
    topology_transition: AttentionLayoutTopologyTransition | None = Field(default=None)
    section_states: list[AttentionLayoutTransitionSection] = Field(default_factory=list)

    # Attributes
    client_intent_id: str
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="layout")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.layout_transitions")
    previous_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionLayoutTransition.previous_transition"
    )
    topology_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionLayoutTransition.topology_transition"
    )

    async def attach_section_state(
        self,
        attention_session_section_id: UUID,
        order: int,
        weight_micros: int,
        is_visible: bool = True,
        is_collapsed: bool = False,
    ) -> AttentionLayoutTransitionSection:
        """
        Construct one typed row through its immutable transition parent.

        This constructor is an internal composition primitive. The public
        atomic boundary remains AttentionSessionLayout.apply_layout_transition.
        """

        payload = {
            "attention_session_section_id": attention_session_section_id,
            "order": order,
            "weight_micros": weight_micros,
            "is_visible": is_visible,
            "is_collapsed": is_collapsed,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_section_state", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_layout_transition_section import (
            AttentionLayoutTransitionSection,
        )

        if isinstance(value, AttentionLayoutTransitionSection):
            return value
        return AttentionLayoutTransitionSection.validate_invocation_value(value)

    @classmethod
    async def create_via_attention_session_layout(
        cls,
        attention_session_layout_id: UUID,
        client_intent_id: str,
        previous_transition_id: UUID | None = None,
        topology_transition_id: UUID | None = None,
        sequence: int = 0,
        transition_kind: str = "layout",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> AttentionLayoutTransition:
        """
        Create one immutable layout-transition header.

        The owning AttentionSessionLayout plus client_intent_id provide stable
        replay identity. Section-state rows are constructed only after the
        parent handler validates the complete vector.
        """

        payload = {
            "attention_session_layout_id": attention_session_layout_id,
            "client_intent_id": client_intent_id,
            "previous_transition_id": previous_transition_id,
            "topology_transition_id": topology_transition_id,
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
        if isinstance(value, AttentionLayoutTransition):
            return value
        return AttentionLayoutTransition.validate_invocation_value(value)


class AttentionLayoutTransitionAttachSectionStateInput(BaseModel):
    attention_session_section_id: UUID
    order: int
    weight_micros: int
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)


class AttentionLayoutTransitionAttachSectionStateOutput(BaseModel):
    value: AttentionLayoutTransitionSection


class AttentionLayoutTransitionCreateViaAttentionSessionLayoutInput(BaseModel):
    attention_session_layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.layout_transitions")
    client_intent_id: str
    previous_transition_id: UUID | None = Field(default=None)
    topology_transition_id: UUID | None = Field(default=None)
    sequence: int = Field(default=0)
    transition_kind: str = Field(default="layout")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class AttentionLayoutTransitionCreateViaAttentionSessionLayoutOutput(BaseModel):
    value: AttentionLayoutTransition


FUNCTIONS = {
    "AttentionLayoutTransition": {
        "attach_section_state": {
            "canonical": {
                "name": "attach_section_state",
                "description": "Construct one typed row through its immutable transition parent.\n\nThis constructor is an internal composition primitive. The public\natomic boundary remains AttentionSessionLayout.apply_layout_transition.",
                "is_constructor": False,
            },
            "input": AttentionLayoutTransitionAttachSectionStateInput,
            "output": AttentionLayoutTransitionAttachSectionStateOutput,
        },
        "create_via_attention_session_layout": {
            "canonical": {
                "name": "create_via_attention_session_layout",
                "description": "Create one immutable layout-transition header.\n\nThe owning AttentionSessionLayout plus client_intent_id provide stable\nreplay identity. Section-state rows are constructed only after the\nparent handler validates the complete vector.",
                "is_constructor": True,
            },
            "input": AttentionLayoutTransitionCreateViaAttentionSessionLayoutInput,
            "output": AttentionLayoutTransitionCreateViaAttentionSessionLayoutOutput,
        },
    },
}

__all__ = [
    "AttentionLayoutTransition",
    "AttentionLayoutTransitionAttachSectionStateInput",
    "AttentionLayoutTransitionAttachSectionStateOutput",
    "AttentionLayoutTransitionCreateViaAttentionSessionLayoutInput",
    "AttentionLayoutTransitionCreateViaAttentionSessionLayoutOutput",
    "FUNCTIONS",
]
