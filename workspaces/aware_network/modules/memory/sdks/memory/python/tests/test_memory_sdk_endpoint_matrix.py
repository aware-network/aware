from __future__ import annotations

from memory_endpoint_matrix import MEMORY_SDK_ENDPOINTS


def test_memory_sdk_endpoint_matrix_contains_working_memory_operations() -> None:
    assert len(MEMORY_SDK_ENDPOINTS) == 13
    assert [name for name, _ in MEMORY_SDK_ENDPOINTS] == [
        "ensure_memory_working",
        "describe_memory_working",
        "list_memory_working_items",
        "validate_memory_working_item",
        "resolve_memory_context",
        "resolve_actor_memory_context",
        "watch_actor_memory_context",
        "resolve_actor_memory_context_frame",
        "watch_actor_memory_context_frame",
        "remember_attention_transition",
        "remember_content",
        "remember_event",
        "record_resolved_event_meaning",
    ]
