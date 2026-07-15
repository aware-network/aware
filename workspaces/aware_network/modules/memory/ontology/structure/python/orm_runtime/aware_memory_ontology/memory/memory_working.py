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
    from aware_content_ontology.chain.content_chain import ContentChain
    from aware_identity_ontology.actor.actor import Actor
    from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem


class MemoryWorking(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    content_chain: ContentChain | None = Field(default=None, exclude=True)
    items: list[MemoryWorkingItem] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for MemoryWorking.actor")
    content_chain_id: UUID = Field(description="Foreign key for MemoryWorking.content_chain")

    @classmethod
    async def build(cls, actor_id: UUID, key: str = "default") -> MemoryWorking:
        """
        Create one deterministic standalone MemoryWorking lane for an Identity Actor.

        Policy:
        - Memory owns the lane object and references Identity Actor relationally.
        - Stable identity is actor plus `key`.
        - The lane may be branched/forked without collapsing into non-branchable Actor identity.
        - ContentChain must be created via ContentChain.build (no direct instantiation).
        """

        payload = {"actor_id": actor_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryWorking):
            return value
        return MemoryWorking.validate_invocation_value(value)

    async def create_item(
        self,
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
        """
        Construct one item under this MemoryWorking lane.

        Contract:
        - Parent->child containment is explicit (`items.build`) so propagation
          can mark `memory_working_id` as child identity rail.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="create_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem

        if isinstance(value, MemoryWorkingItem):
            return value
        return MemoryWorkingItem.validate_invocation_value(value)

    async def add_event_item(
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
        rationale: str | None = None,
        summary: str | None = None,
    ) -> MemoryWorkingItem:
        """Appends an `event` memory item."""

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
            "rationale": rationale,
            "summary": summary,
        }
        result = await invoke_instance(orm_model=self, function_name="add_event_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem

        if isinstance(value, MemoryWorkingItem):
            return value
        return MemoryWorkingItem.validate_invocation_value(value)

    async def add_content_item(
        self, content_id: UUID, rationale: str | None = None, summary: str | None = None
    ) -> MemoryWorkingItem:
        """Appends a `content` memory item."""

        payload = {"content_id": content_id, "rationale": rationale, "summary": summary}
        result = await invoke_instance(orm_model=self, function_name="add_content_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem

        if isinstance(value, MemoryWorkingItem):
            return value
        return MemoryWorkingItem.validate_invocation_value(value)

    async def add_tool_item(
        self,
        tool_call_id: UUID,
        tool_response_id: UUID | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        projection_hash: str | None = None,
        rationale: str | None = None,
        summary: str | None = None,
    ) -> MemoryWorkingItem:
        """Appends a `tool` memory item."""

        payload = {
            "tool_call_id": tool_call_id,
            "tool_response_id": tool_response_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "projection_hash": projection_hash,
            "rationale": rationale,
            "summary": summary,
        }
        result = await invoke_instance(orm_model=self, function_name="add_tool_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem

        if isinstance(value, MemoryWorkingItem):
            return value
        return MemoryWorkingItem.validate_invocation_value(value)

    async def add_attention_item(
        self, attention_focus_transition_id: UUID, rationale: str | None = None, summary: str | None = None
    ) -> MemoryWorkingItem:
        """
        Appends an `attention` memory item by retaining an Attention-owned
        focus transition.
        """

        payload = {
            "attention_focus_transition_id": attention_focus_transition_id,
            "rationale": rationale,
            "summary": summary,
        }
        result = await invoke_instance(orm_model=self, function_name="add_attention_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem

        if isinstance(value, MemoryWorkingItem):
            return value
        return MemoryWorkingItem.validate_invocation_value(value)


class MemoryWorkingBuildInput(BaseModel):
    actor_id: UUID
    key: str = Field(default="default")


class MemoryWorkingBuildOutput(BaseModel):
    value: MemoryWorking


class MemoryWorkingCreateItemInput(BaseModel):
    kind: MemoryWorkingItemKind
    position: int
    created_at: datetime | None = Field(default=None)
    event_frame_id: UUID | None = Field(default=None)
    content_frame_id: UUID | None = Field(default=None)
    tool_frame_id: UUID | None = Field(default=None)
    attention_transition_id: UUID | None = Field(default=None)
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class MemoryWorkingCreateItemOutput(BaseModel):
    value: MemoryWorkingItem


class MemoryWorkingAddEventItemInput(BaseModel):
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
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class MemoryWorkingAddEventItemOutput(BaseModel):
    value: MemoryWorkingItem


class MemoryWorkingAddContentItemInput(BaseModel):
    content_id: UUID
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class MemoryWorkingAddContentItemOutput(BaseModel):
    value: MemoryWorkingItem


class MemoryWorkingAddToolItemInput(BaseModel):
    tool_call_id: UUID
    tool_response_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class MemoryWorkingAddToolItemOutput(BaseModel):
    value: MemoryWorkingItem


class MemoryWorkingAddAttentionItemInput(BaseModel):
    attention_focus_transition_id: UUID
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class MemoryWorkingAddAttentionItemOutput(BaseModel):
    value: MemoryWorkingItem


FUNCTIONS = {
    "MemoryWorking": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic standalone MemoryWorking lane for an Identity Actor.\n\nPolicy:\n- Memory owns the lane object and references Identity Actor relationally.\n- Stable identity is actor plus `key`.\n- The lane may be branched/forked without collapsing into non-branchable Actor identity.\n- ContentChain must be created via ContentChain.build (no direct instantiation).",
                "is_constructor": True,
            },
            "input": MemoryWorkingBuildInput,
            "output": MemoryWorkingBuildOutput,
        },
        "create_item": {
            "canonical": {
                "name": "create_item",
                "description": "Construct one item under this MemoryWorking lane.\n\nContract:\n- Parent->child containment is explicit (`items.build`) so propagation\n  can mark `memory_working_id` as child identity rail.",
                "is_constructor": False,
            },
            "input": MemoryWorkingCreateItemInput,
            "output": MemoryWorkingCreateItemOutput,
        },
        "add_event_item": {
            "canonical": {
                "name": "add_event_item",
                "description": "Appends an `event` memory item.",
                "is_constructor": False,
            },
            "input": MemoryWorkingAddEventItemInput,
            "output": MemoryWorkingAddEventItemOutput,
        },
        "add_content_item": {
            "canonical": {
                "name": "add_content_item",
                "description": "Appends a `content` memory item.",
                "is_constructor": False,
            },
            "input": MemoryWorkingAddContentItemInput,
            "output": MemoryWorkingAddContentItemOutput,
        },
        "add_tool_item": {
            "canonical": {
                "name": "add_tool_item",
                "description": "Appends a `tool` memory item.",
                "is_constructor": False,
            },
            "input": MemoryWorkingAddToolItemInput,
            "output": MemoryWorkingAddToolItemOutput,
        },
        "add_attention_item": {
            "canonical": {
                "name": "add_attention_item",
                "description": "Appends an `attention` memory item by retaining an Attention-owned\nfocus transition.",
                "is_constructor": False,
            },
            "input": MemoryWorkingAddAttentionItemInput,
            "output": MemoryWorkingAddAttentionItemOutput,
        },
    },
}

__all__ = [
    "MemoryWorking",
    "MemoryWorkingBuildInput",
    "MemoryWorkingBuildOutput",
    "MemoryWorkingCreateItemInput",
    "MemoryWorkingCreateItemOutput",
    "MemoryWorkingAddEventItemInput",
    "MemoryWorkingAddEventItemOutput",
    "MemoryWorkingAddContentItemInput",
    "MemoryWorkingAddContentItemOutput",
    "MemoryWorkingAddToolItemInput",
    "MemoryWorkingAddToolItemOutput",
    "MemoryWorkingAddAttentionItemInput",
    "MemoryWorkingAddAttentionItemOutput",
    "FUNCTIONS",
]
