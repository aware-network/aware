from __future__ import annotations

from aware_memory_ontology.memory.memory_working_content_frame import (
    MemoryWorkingContentFrame,
)
from aware_memory_ontology.memory.memory_working_event_frame import (
    MemoryWorkingEventFrame,
)
from aware_memory_ontology.memory.memory_working_item import MemoryWorkingItem
from aware_memory_ontology.memory.memory_working_item_enums import (
    MemoryWorkingItemKind,
)
from aware_memory_ontology.memory.memory_working_tool_frame import (
    MemoryWorkingToolFrame,
)

_EVENT_FRAME_PROVENANCE_FIELDS = (
    "event_config_id",
    "event_activation_id",
    "event_type",
    "event_source",
    "event_status",
    "commit_branch_id",
    "commit_projection_hash",
    "commit_id",
    "object_instance_graph_id",
    "object_instance_graph_commit_id",
    "action_intent_id",
    "intent_key",
    "action_config_id",
    "action_execution_id",
    "action_execution_key",
    "api_call_key",
    "action_binding_id",
    "action_experience_id",
    "environment_profile_id",
    "environment_event_id",
    "invocation_config_id",
    "endpoint_id",
    "actor_subscription_id",
)


def require_working_item_kind(
    memory_working_item: MemoryWorkingItem,
    expected: MemoryWorkingItemKind,
) -> None:
    actual = memory_working_item.kind
    if actual != expected:
        raise ValueError(
            "MemoryWorkingItem frame kind mismatch: "
            f"item_id={memory_working_item.id} expected_kind={expected.value} "
            f"actual_kind={actual.value}"
        )


def resolve_event_frame(
    memory_working_item: MemoryWorkingItem,
) -> MemoryWorkingEventFrame | None:
    return memory_working_item.event_frame


def resolve_content_frame(
    memory_working_item: MemoryWorkingItem,
) -> MemoryWorkingContentFrame | None:
    return memory_working_item.content_frame


def resolve_tool_frame(
    memory_working_item: MemoryWorkingItem,
) -> MemoryWorkingToolFrame | None:
    return memory_working_item.tool_frame


def require_matching_event_frame(
    *,
    existing: MemoryWorkingEventFrame,
    built: MemoryWorkingEventFrame,
) -> None:
    if existing.id != built.id:
        raise ValueError(
            "MemoryWorkingItem.create_event_frame deterministic id mismatch: "
            f"expected={existing.id} got={built.id}"
        )
    if existing.event_id != built.event_id:
        raise ValueError(
            "MemoryWorkingItem.create_event_frame payload mismatch on event_id: "
            f"expected={existing.event_id} got={built.event_id}"
        )
    for field_name in _EVENT_FRAME_PROVENANCE_FIELDS:
        existing_value = getattr(existing, field_name, None)
        built_value = getattr(built, field_name, None)
        if existing_value != built_value:
            raise ValueError(
                "MemoryWorkingItem.create_event_frame payload mismatch on "
                f"{field_name}: expected={existing_value!r} got={built_value!r}"
            )


def require_matching_content_frame(
    *,
    existing: MemoryWorkingContentFrame,
    built: MemoryWorkingContentFrame,
) -> None:
    if existing.id != built.id:
        raise ValueError(
            "MemoryWorkingItem.create_content_frame deterministic id mismatch: "
            f"expected={existing.id} got={built.id}"
        )
    if existing.content_id != built.content_id:
        raise ValueError(
            "MemoryWorkingItem.create_content_frame payload mismatch on content_id: "
            f"expected={existing.content_id} got={built.content_id}"
        )


def require_matching_tool_frame(
    *,
    existing: MemoryWorkingToolFrame,
    built: MemoryWorkingToolFrame,
) -> None:
    if existing.id != built.id:
        raise ValueError(
            "MemoryWorkingItem.create_tool_frame deterministic id mismatch: "
            f"expected={existing.id} got={built.id}"
        )
    if existing.tool_call_id != built.tool_call_id:
        raise ValueError(
            "MemoryWorkingItem.create_tool_frame payload mismatch on tool_call_id: "
            f"expected={existing.tool_call_id} got={built.tool_call_id}"
        )
    if existing.tool_response_id != built.tool_response_id:
        raise ValueError(
            "MemoryWorkingItem.create_tool_frame payload mismatch on tool_response_id: "
            f"expected={existing.tool_response_id} got={built.tool_response_id}"
        )
    if existing.object_instance_graph_branch_id != built.object_instance_graph_branch_id:
        raise ValueError(
            "MemoryWorkingItem.create_tool_frame payload mismatch on "
            "object_instance_graph_branch_id: "
            f"expected={existing.object_instance_graph_branch_id} "
            f"got={built.object_instance_graph_branch_id}"
        )
    if existing.projection_hash != built.projection_hash:
        raise ValueError(
            "MemoryWorkingItem.create_tool_frame payload mismatch on projection_hash: "
            f"expected={existing.projection_hash!r} got={built.projection_hash!r}"
        )


__all__ = [
    "require_matching_content_frame",
    "require_matching_event_frame",
    "require_matching_tool_frame",
    "require_working_item_kind",
    "resolve_content_frame",
    "resolve_event_frame",
    "resolve_tool_frame",
]
