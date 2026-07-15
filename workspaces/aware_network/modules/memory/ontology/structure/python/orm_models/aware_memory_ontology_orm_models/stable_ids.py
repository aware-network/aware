# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_MEMORY = uuid5(NAMESPACE_URL, "aware://memory/v1")


def stable_memory_episode_id(*, content_chain_content_id: UUID, content_chain_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_chain_content_id, content_chain_section_id"""

    return uuid5(NS_MEMORY, f"aware:memory_episode:{content_chain_content_id}:{content_chain_section_id}")


def stable_memory_episodic_id(*, actor_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_MEMORY, f"aware:memory_episodic:{actor_id}:{key_norm}")


def stable_memory_procedural_id(*, identity_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_MEMORY, f"aware:memory_procedural:{identity_id}:{key_norm}")


def stable_memory_procedure_id(*, content_id: UUID, procedure_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_id, procedure_config_id"""

    return uuid5(NS_MEMORY, f"aware:memory_procedure:{content_id}:{procedure_config_id}")


def stable_memory_procedure_config_id(*, content_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_id"""

    return uuid5(NS_MEMORY, f"aware:memory_procedure_config:{content_id}")


def stable_memory_procedure_episode_id(*, memory_episode_id: UUID, memory_procedure_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: memory_episode_id, memory_procedure_id"""

    return uuid5(NS_MEMORY, f"aware:memory_procedure_episode:{memory_episode_id}:{memory_procedure_id}")


def stable_memory_semantic_id(*, identity_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_MEMORY, f"aware:memory_semantic:{identity_id}:{key_norm}")


def stable_memory_working_id(*, actor_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_MEMORY, f"aware:memory_working:{actor_id}:{key_norm}")


def stable_memory_working_content_frame_id(*, memory_working_item_id: UUID, content_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: memory_working_item_id, content_id"""

    return uuid5(NS_MEMORY, f"aware:memory_working_content_frame:{memory_working_item_id}:{content_id}")


def stable_memory_working_event_frame_id(*, memory_working_item_id: UUID, event_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: memory_working_item_id, event_id"""

    return uuid5(NS_MEMORY, f"aware:memory_working_event_frame:{memory_working_item_id}:{event_id}")


def stable_memory_working_event_meaning_id(
    *, memory_working_event_frame_id: UUID, resolver_api_call_outcome_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: memory_working_event_frame_id, resolver_api_call_outcome_id"""

    return uuid5(
        NS_MEMORY, f"aware:memory_working_event_meaning:{memory_working_event_frame_id}:{resolver_api_call_outcome_id}"
    )


def stable_memory_working_item_id(*, memory_working_id: UUID, kind: str, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: memory_working_id, kind, position"""

    kind_norm = (kind or "").casefold().strip()
    return uuid5(NS_MEMORY, f"aware:memory_working_item:{memory_working_id}:{kind_norm}:{position}")


def stable_memory_working_tool_frame_id(*, memory_working_item_id: UUID, tool_call_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: memory_working_item_id, tool_call_id"""

    return uuid5(NS_MEMORY, f"aware:memory_working_tool_frame:{memory_working_item_id}:{tool_call_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "2da4bc56-0460-5dd6-88b6-fb28692a12b5": ("stable_memory_episodic_id", ("actor_id", "key")),
    "2edd883f-2452-5e1b-8509-8e0c87243393": (
        "stable_memory_working_event_meaning_id",
        ("memory_working_event_frame_id", "resolver_api_call_outcome_id"),
    ),
    "31e7c155-5c1e-57c5-a246-d652ff05483c": (
        "stable_memory_working_item_id",
        ("memory_working_id", "kind", "position"),
    ),
    "49be773d-7588-57ae-a79e-3449ca996340": ("stable_memory_working_id", ("actor_id", "key")),
    "6f201434-d0c3-5ccb-b3b7-06b6b525d7a8": ("stable_memory_procedural_id", ("identity_id", "key")),
    "9ab5b299-2f42-5e71-a3a7-61b3f5922938": (
        "stable_memory_working_event_frame_id",
        ("memory_working_item_id", "event_id"),
    ),
    "a0f5eecb-d1ad-5b99-8eb7-a328ec0a02ca": (
        "stable_memory_working_tool_frame_id",
        ("memory_working_item_id", "tool_call_id"),
    ),
    "c42b8975-9d76-5011-b473-90558a3f3a36": (
        "stable_memory_working_content_frame_id",
        ("memory_working_item_id", "content_id"),
    ),
    "efa76b72-1c14-519d-9b93-889603eed4bb": ("stable_memory_semantic_id", ("identity_id", "key")),
}

__all__ = [
    "stable_memory_episode_id",
    "stable_memory_episodic_id",
    "stable_memory_procedural_id",
    "stable_memory_procedure_id",
    "stable_memory_procedure_config_id",
    "stable_memory_procedure_episode_id",
    "stable_memory_semantic_id",
    "stable_memory_working_id",
    "stable_memory_working_content_frame_id",
    "stable_memory_working_event_frame_id",
    "stable_memory_working_event_meaning_id",
    "stable_memory_working_item_id",
    "stable_memory_working_tool_frame_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
