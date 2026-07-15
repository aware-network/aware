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

# Memory Ontology
from aware_memory_ontology.memory.memory_working_item_enums import MemoryWorkingItemKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition
    from aware_memory_ontology.memory.memory_working_content_frame import MemoryWorkingContentFrame
    from aware_memory_ontology.memory.memory_working_event_frame import MemoryWorkingEventFrame
    from aware_memory_ontology.memory.memory_working_tool_frame import MemoryWorkingToolFrame


class MemoryWorkingItem(ORMModel):
    """
    Typed working-memory item for attention-first actor context.
    Contract:
    - One item captures one canonical dynamic axis:
    `event`, `content`, `tool`, or `attention`.
    - `MemoryWorking` owns item ordering (`position`).
    - Attention items point at Attention-owned transition source truth.
    Memory must not duplicate focus/layout/view envelopes.
    """

    # Relationships
    event_frame: MemoryWorkingEventFrame | None = Field(default=None, exclude=True)
    content_frame: MemoryWorkingContentFrame | None = Field(default=None, exclude=True)
    tool_frame: MemoryWorkingToolFrame | None = Field(default=None, exclude=True)
    attention_transition: AttentionFocusTransition | None = Field(default=None, exclude=True)

    # Attributes
    kind: MemoryWorkingItemKind
    position: int
    created_at: datetime
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)

    # Foreign Keys
    memory_working_id: UUID = Field(description="Foreign key for MemoryWorking.items")
    attention_transition_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingItem.attention_transition"
    )

    async def create_event_frame(
        self,
        event_id: UUID,
        event_config_id: UUID | None = None,
        event_activation_id: UUID | None = None,
        event_type: str | None = None,
        event_source: str | None = None,
        event_status: str | None = None,
        commit_branch_id: UUID | None = None,
        commit_projection_hash: str | None = None,
        commit_id: UUID | None = None,
        object_instance_graph_id: UUID | None = None,
        object_instance_graph_commit_id: UUID | None = None,
        action_intent_id: UUID | None = None,
        intent_key: str | None = None,
        action_config_id: UUID | None = None,
        action_execution_id: UUID | None = None,
        action_execution_key: str | None = None,
        api_call_key: UUID | None = None,
        action_binding_id: UUID | None = None,
        action_experience_id: UUID | None = None,
        environment_profile_id: UUID | None = None,
        environment_event_id: UUID | None = None,
        invocation_config_id: UUID | None = None,
        endpoint_id: UUID | None = None,
        actor_subscription_id: UUID | None = None,
    ) -> MemoryWorkingEventFrame:
        """Construct one event frame under this item (kind=event)."""

        payload = {
            "event_id": event_id,
            "event_config_id": event_config_id,
            "event_activation_id": event_activation_id,
            "event_type": event_type,
            "event_source": event_source,
            "event_status": event_status,
            "commit_branch_id": commit_branch_id,
            "commit_projection_hash": commit_projection_hash,
            "commit_id": commit_id,
            "object_instance_graph_id": object_instance_graph_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "action_intent_id": action_intent_id,
            "intent_key": intent_key,
            "action_config_id": action_config_id,
            "action_execution_id": action_execution_id,
            "action_execution_key": action_execution_key,
            "api_call_key": api_call_key,
            "action_binding_id": action_binding_id,
            "action_experience_id": action_experience_id,
            "environment_profile_id": environment_profile_id,
            "environment_event_id": environment_event_id,
            "invocation_config_id": invocation_config_id,
            "endpoint_id": endpoint_id,
            "actor_subscription_id": actor_subscription_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_event_frame", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_event_frame import MemoryWorkingEventFrame

        if isinstance(value, MemoryWorkingEventFrame):
            return value
        return MemoryWorkingEventFrame.validate_invocation_value(value)

    async def create_content_frame(self, content_id: UUID) -> MemoryWorkingContentFrame:
        """Construct one content frame under this item (kind=content)."""

        payload = {"content_id": content_id}
        result = await invoke_instance(orm_model=self, function_name="create_content_frame", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_content_frame import MemoryWorkingContentFrame

        if isinstance(value, MemoryWorkingContentFrame):
            return value
        return MemoryWorkingContentFrame.validate_invocation_value(value)

    async def create_tool_frame(
        self,
        tool_call_id: UUID,
        tool_response_id: UUID | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> MemoryWorkingToolFrame:
        """Construct one tool frame under this item (kind=tool)."""

        payload = {
            "tool_call_id": tool_call_id,
            "tool_response_id": tool_response_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "projection_hash": projection_hash,
        }
        result = await invoke_instance(orm_model=self, function_name="create_tool_frame", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_tool_frame import MemoryWorkingToolFrame

        if isinstance(value, MemoryWorkingToolFrame):
            return value
        return MemoryWorkingToolFrame.validate_invocation_value(value)

    async def link_attention_transition(self, attention_focus_transition_id: UUID) -> AttentionFocusTransition:
        """
        Link this memory item to one Attention-owned focus transition.

        Memory records retention of the transition; it does not copy the
        transition's focus/layout/view envelope.
        """

        payload = {"attention_focus_transition_id": attention_focus_transition_id}
        result = await invoke_instance(orm_model=self, function_name="link_attention_transition", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_focus_transition import AttentionFocusTransition

        if isinstance(value, AttentionFocusTransition):
            return value
        return AttentionFocusTransition.validate_invocation_value(value)

    @classmethod
    async def build_via_memory_working(
        cls,
        memory_working_id: UUID,
        kind: MemoryWorkingItemKind,
        position: int,
        created_at: datetime | None = None,
        event_frame_id: UUID | None = None,
        content_frame_id: UUID | None = None,
        tool_frame_id: UUID | None = None,
        attention_transition_id: UUID | None = None,
        rationale: str | None = None,
        summary: str | None = None,
    ) -> MemoryWorkingItem:
        """Builds a deterministic MemoryWorkingItem envelope."""

        payload = {
            "memory_working_id": memory_working_id,
            "kind": kind,
            "position": position,
            "created_at": created_at,
            "event_frame_id": event_frame_id,
            "content_frame_id": content_frame_id,
            "tool_frame_id": tool_frame_id,
            "attention_transition_id": attention_transition_id,
            "rationale": rationale,
            "summary": summary,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_memory_working", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryWorkingItem):
            return value
        return MemoryWorkingItem.validate_invocation_value(value)


class MemoryWorkingItemCreateEventFrameInput(BaseModel):
    event_id: UUID
    event_config_id: UUID | None = Field(default=None)
    event_activation_id: UUID | None = Field(default=None)
    event_type: str | None = Field(default=None)
    event_source: str | None = Field(default=None)
    event_status: str | None = Field(default=None)
    commit_branch_id: UUID | None = Field(default=None)
    commit_projection_hash: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    action_intent_id: UUID | None = Field(default=None)
    intent_key: str | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_execution_id: UUID | None = Field(default=None)
    action_execution_key: str | None = Field(default=None)
    api_call_key: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_experience_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_event_id: UUID | None = Field(default=None)
    invocation_config_id: UUID | None = Field(default=None)
    endpoint_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)


class MemoryWorkingItemCreateEventFrameOutput(BaseModel):
    value: MemoryWorkingEventFrame


class MemoryWorkingItemCreateContentFrameInput(BaseModel):
    content_id: UUID


class MemoryWorkingItemCreateContentFrameOutput(BaseModel):
    value: MemoryWorkingContentFrame


class MemoryWorkingItemCreateToolFrameInput(BaseModel):
    tool_call_id: UUID
    tool_response_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)


class MemoryWorkingItemCreateToolFrameOutput(BaseModel):
    value: MemoryWorkingToolFrame


class MemoryWorkingItemLinkAttentionTransitionInput(BaseModel):
    attention_focus_transition_id: UUID


class MemoryWorkingItemLinkAttentionTransitionOutput(BaseModel):
    value: AttentionFocusTransition


class MemoryWorkingItemBuildViaMemoryWorkingInput(BaseModel):
    memory_working_id: UUID = Field(description="Foreign key for MemoryWorking.items")
    kind: MemoryWorkingItemKind
    position: int
    created_at: datetime | None = Field(default=None)
    event_frame_id: UUID | None = Field(default=None)
    content_frame_id: UUID | None = Field(default=None)
    tool_frame_id: UUID | None = Field(default=None)
    attention_transition_id: UUID | None = Field(default=None)
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class MemoryWorkingItemBuildViaMemoryWorkingOutput(BaseModel):
    value: MemoryWorkingItem


FUNCTIONS = {
    "MemoryWorkingItem": {
        "create_event_frame": {
            "canonical": {
                "name": "create_event_frame",
                "description": "Construct one event frame under this item (kind=event).",
                "is_constructor": False,
            },
            "input": MemoryWorkingItemCreateEventFrameInput,
            "output": MemoryWorkingItemCreateEventFrameOutput,
        },
        "create_content_frame": {
            "canonical": {
                "name": "create_content_frame",
                "description": "Construct one content frame under this item (kind=content).",
                "is_constructor": False,
            },
            "input": MemoryWorkingItemCreateContentFrameInput,
            "output": MemoryWorkingItemCreateContentFrameOutput,
        },
        "create_tool_frame": {
            "canonical": {
                "name": "create_tool_frame",
                "description": "Construct one tool frame under this item (kind=tool).",
                "is_constructor": False,
            },
            "input": MemoryWorkingItemCreateToolFrameInput,
            "output": MemoryWorkingItemCreateToolFrameOutput,
        },
        "link_attention_transition": {
            "canonical": {
                "name": "link_attention_transition",
                "description": "Link this memory item to one Attention-owned focus transition.\n\nMemory records retention of the transition; it does not copy the\ntransition's focus/layout/view envelope.",
                "is_constructor": False,
            },
            "input": MemoryWorkingItemLinkAttentionTransitionInput,
            "output": MemoryWorkingItemLinkAttentionTransitionOutput,
        },
        "build_via_memory_working": {
            "canonical": {
                "name": "build_via_memory_working",
                "description": "Builds a deterministic MemoryWorkingItem envelope.",
                "is_constructor": True,
            },
            "input": MemoryWorkingItemBuildViaMemoryWorkingInput,
            "output": MemoryWorkingItemBuildViaMemoryWorkingOutput,
        },
    },
}

__all__ = [
    "MemoryWorkingItem",
    "MemoryWorkingItemCreateEventFrameInput",
    "MemoryWorkingItemCreateEventFrameOutput",
    "MemoryWorkingItemCreateContentFrameInput",
    "MemoryWorkingItemCreateContentFrameOutput",
    "MemoryWorkingItemCreateToolFrameInput",
    "MemoryWorkingItemCreateToolFrameOutput",
    "MemoryWorkingItemLinkAttentionTransitionInput",
    "MemoryWorkingItemLinkAttentionTransitionOutput",
    "MemoryWorkingItemBuildViaMemoryWorkingInput",
    "MemoryWorkingItemBuildViaMemoryWorkingOutput",
    "FUNCTIONS",
]
