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
    from aware_attention_ontology.layout.layout import Layout
    from aware_attention_ontology.layout.layout_config import LayoutConfig
    from aware_attention_ontology.session.attention_layout_topology_transition import AttentionLayoutTopologyTransition
    from aware_attention_ontology.session.attention_layout_transition import AttentionLayoutTransition
    from aware_attention_ontology.session.attention_session_section import AttentionSessionSection


class AttentionSessionLayout(ORMModel):
    """
    Session-local mounted Attention Layout.
    Contract:
    - Parent constructor is AttentionSession.
    - Layout/LayoutConfig remain Attention topology authorities.
    - Session layout state is local to AttentionSession.
    """

    # Relationships
    layout: Layout | None = Field(default=None)
    layout_config: LayoutConfig | None = Field(default=None)
    sections: list[AttentionSessionSection] = Field(default_factory=list)
    active_section: AttentionSessionSection | None = Field(default=None)
    topology_transitions: list[AttentionLayoutTopologyTransition] = Field(default_factory=list)
    active_topology_transition: AttentionLayoutTopologyTransition | None = Field(default=None)
    layout_transitions: list[AttentionLayoutTransition] = Field(default_factory=list)
    active_layout_transition: AttentionLayoutTransition | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)

    # Foreign Keys
    attention_session_id: UUID = Field(description="Foreign key for AttentionSession.layouts")
    layout_id: UUID = Field(description="Foreign key for AttentionSessionLayout.layout")
    layout_config_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.layout_config"
    )
    active_section_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.active_section"
    )
    active_topology_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.active_topology_transition"
    )
    active_layout_transition_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionSessionLayout.active_layout_transition"
    )

    async def attach_section(
        self,
        layout_section_id: UUID,
        section_id: UUID,
        section_key: str | None = None,
        order: int = 0,
        is_active: bool = True,
    ) -> AttentionSessionSection:
        """
        Add one session-local section state row.

        Contract:
        - The row is grounded by LayoutSection and Section.
        - Focus transition history must hang under this section row.
        """

        payload = {
            "layout_section_id": layout_section_id,
            "section_id": section_id,
            "section_key": section_key,
            "order": order,
            "is_active": is_active,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_session_section import AttentionSessionSection

        if isinstance(value, AttentionSessionSection):
            return value
        return AttentionSessionSection.validate_invocation_value(value)

    async def set_active_section(self, attention_session_section_id: UUID) -> AttentionSessionSection:
        """Select the active session-local section."""

        payload = {"attention_session_section_id": attention_session_section_id}
        result = await invoke_instance(orm_model=self, function_name="set_active_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_session_section import AttentionSessionSection

        if isinstance(value, AttentionSessionSection):
            return value
        return AttentionSessionSection.validate_invocation_value(value)

    async def apply_topology_transition(
        self,
        client_intent_id: str,
        section_states_json: JsonObject,
        expected_previous_topology_transition_id: UUID | None = None,
        transition_kind: str = "topology",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> AttentionLayoutTopologyTransition:
        """
        Atomically append one immutable full-vector layout topology transition.

        Contract:
        - AttentionSessionSection rows are stable admitted anchors.
        - The complete ordered active membership is supplied on every intent.
        - Omitted anchors remain available to history and may be re-added.
        - expected_previous_topology_transition_id is an exact active-head CAS.
        - Repeating the active client intent with the identical payload is a
          no-op; reusing it with different content fails closed.
        """

        payload = {
            "client_intent_id": client_intent_id,
            "section_states_json": section_states_json,
            "expected_previous_topology_transition_id": expected_previous_topology_transition_id,
            "transition_kind": transition_kind,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="apply_topology_transition", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_layout_topology_transition import (
            AttentionLayoutTopologyTransition,
        )

        if isinstance(value, AttentionLayoutTopologyTransition):
            return value
        return AttentionLayoutTopologyTransition.validate_invocation_value(value)

    async def apply_layout_transition(
        self,
        client_intent_id: str,
        section_states_json: JsonObject,
        expected_previous_layout_transition_id: UUID | None = None,
        topology_transition_id: UUID | None = None,
        transition_kind: str = "layout",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> AttentionLayoutTransition:
        """
        Atomically append one immutable full-vector shared-layout transition.

        Contract:
        - The invocation envelope is validated before construction and is not
          persisted as shared layout authority.
        - One typed state row is committed for every mounted session section.
        - expected_previous_layout_transition_id is an exact active-head CAS.
        - topology_transition_id must exactly pin the active explicit topology;
          legacy fixed layouts use a null topology pin.
        - Repeating the active client intent with the identical payload is a
          no-op; reusing it with different content fails closed.
        """

        payload = {
            "client_intent_id": client_intent_id,
            "section_states_json": section_states_json,
            "expected_previous_layout_transition_id": expected_previous_layout_transition_id,
            "topology_transition_id": topology_transition_id,
            "transition_kind": transition_kind,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="apply_layout_transition", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_layout_transition import AttentionLayoutTransition

        if isinstance(value, AttentionLayoutTransition):
            return value
        return AttentionLayoutTransition.validate_invocation_value(value)

    @classmethod
    async def create_via_attention_session(
        cls,
        attention_session_id: UUID,
        layout_id: UUID,
        layout_config_id: UUID | None = None,
        key: str | None = None,
        order: int = 0,
        is_active: bool = True,
    ) -> AttentionSessionLayout:
        """Create a session-local mounted layout."""

        payload = {
            "attention_session_id": attention_session_id,
            "layout_id": layout_id,
            "layout_config_id": layout_config_id,
            "key": key,
            "order": order,
            "is_active": is_active,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_attention_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionSessionLayout):
            return value
        return AttentionSessionLayout.validate_invocation_value(value)


class AttentionSessionLayoutAttachSectionInput(BaseModel):
    layout_section_id: UUID
    section_id: UUID
    section_key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class AttentionSessionLayoutAttachSectionOutput(BaseModel):
    value: AttentionSessionSection


class AttentionSessionLayoutSetActiveSectionInput(BaseModel):
    attention_session_section_id: UUID


class AttentionSessionLayoutSetActiveSectionOutput(BaseModel):
    value: AttentionSessionSection


class AttentionSessionLayoutApplyTopologyTransitionInput(BaseModel):
    client_intent_id: str
    section_states_json: JsonObject
    expected_previous_topology_transition_id: UUID | None = Field(default=None)
    transition_kind: str = Field(default="topology")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class AttentionSessionLayoutApplyTopologyTransitionOutput(BaseModel):
    value: AttentionLayoutTopologyTransition


class AttentionSessionLayoutApplyLayoutTransitionInput(BaseModel):
    client_intent_id: str
    section_states_json: JsonObject
    expected_previous_layout_transition_id: UUID | None = Field(default=None)
    topology_transition_id: UUID | None = Field(default=None)
    transition_kind: str = Field(default="layout")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class AttentionSessionLayoutApplyLayoutTransitionOutput(BaseModel):
    value: AttentionLayoutTransition


class AttentionSessionLayoutCreateViaAttentionSessionInput(BaseModel):
    attention_session_id: UUID = Field(description="Foreign key for AttentionSession.layouts")
    layout_id: UUID
    layout_config_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class AttentionSessionLayoutCreateViaAttentionSessionOutput(BaseModel):
    value: AttentionSessionLayout


FUNCTIONS = {
    "AttentionSessionLayout": {
        "attach_section": {
            "canonical": {
                "name": "attach_section",
                "description": "Add one session-local section state row.\n\nContract:\n- The row is grounded by LayoutSection and Section.\n- Focus transition history must hang under this section row.",
                "is_constructor": False,
            },
            "input": AttentionSessionLayoutAttachSectionInput,
            "output": AttentionSessionLayoutAttachSectionOutput,
        },
        "set_active_section": {
            "canonical": {
                "name": "set_active_section",
                "description": "Select the active session-local section.",
                "is_constructor": False,
            },
            "input": AttentionSessionLayoutSetActiveSectionInput,
            "output": AttentionSessionLayoutSetActiveSectionOutput,
        },
        "apply_topology_transition": {
            "canonical": {
                "name": "apply_topology_transition",
                "description": "Atomically append one immutable full-vector layout topology transition.\n\nContract:\n- AttentionSessionSection rows are stable admitted anchors.\n- The complete ordered active membership is supplied on every intent.\n- Omitted anchors remain available to history and may be re-added.\n- expected_previous_topology_transition_id is an exact active-head CAS.\n- Repeating the active client intent with the identical payload is a\n  no-op; reusing it with different content fails closed.",
                "is_constructor": False,
            },
            "input": AttentionSessionLayoutApplyTopologyTransitionInput,
            "output": AttentionSessionLayoutApplyTopologyTransitionOutput,
        },
        "apply_layout_transition": {
            "canonical": {
                "name": "apply_layout_transition",
                "description": "Atomically append one immutable full-vector shared-layout transition.\n\nContract:\n- The invocation envelope is validated before construction and is not\n  persisted as shared layout authority.\n- One typed state row is committed for every mounted session section.\n- expected_previous_layout_transition_id is an exact active-head CAS.\n- topology_transition_id must exactly pin the active explicit topology;\n  legacy fixed layouts use a null topology pin.\n- Repeating the active client intent with the identical payload is a\n  no-op; reusing it with different content fails closed.",
                "is_constructor": False,
            },
            "input": AttentionSessionLayoutApplyLayoutTransitionInput,
            "output": AttentionSessionLayoutApplyLayoutTransitionOutput,
        },
        "create_via_attention_session": {
            "canonical": {
                "name": "create_via_attention_session",
                "description": "Create a session-local mounted layout.",
                "is_constructor": True,
            },
            "input": AttentionSessionLayoutCreateViaAttentionSessionInput,
            "output": AttentionSessionLayoutCreateViaAttentionSessionOutput,
        },
    },
}

__all__ = [
    "AttentionSessionLayout",
    "AttentionSessionLayoutAttachSectionInput",
    "AttentionSessionLayoutAttachSectionOutput",
    "AttentionSessionLayoutSetActiveSectionInput",
    "AttentionSessionLayoutSetActiveSectionOutput",
    "AttentionSessionLayoutApplyTopologyTransitionInput",
    "AttentionSessionLayoutApplyTopologyTransitionOutput",
    "AttentionSessionLayoutApplyLayoutTransitionInput",
    "AttentionSessionLayoutApplyLayoutTransitionOutput",
    "AttentionSessionLayoutCreateViaAttentionSessionInput",
    "AttentionSessionLayoutCreateViaAttentionSessionOutput",
    "FUNCTIONS",
]
