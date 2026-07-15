# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_ATTENTION = uuid5(NAMESPACE_URL, "aware://attention/v1")


def stable_actor_focus_id(*, actor_id: UUID, focus_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, focus_id"""

    return uuid5(NS_ATTENTION, f"aware:actor_focus:{actor_id}:{focus_id}")


def stable_actor_focus_evidence_id(*, actor_focus_id: UUID, evidence_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_focus_id, evidence_key"""

    evidence_key_norm = (evidence_key or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:actor_focus_evidence:{actor_focus_id}:{evidence_key_norm}")


def stable_actor_focus_request_id(*, sender_id: UUID, receiver_id: UUID, focus_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: sender_id, receiver_id, focus_id"""

    return uuid5(NS_ATTENTION, f"aware:actor_focus_request:{sender_id}:{receiver_id}:{focus_id}")


def stable_actor_focus_request_response_id(*, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_ATTENTION, f"aware:actor_focus_request_response:{key_norm}")


def stable_actor_focus_scope_id(*, actor_id: UUID, focus_scope_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, focus_scope_id"""

    return uuid5(NS_ATTENTION, f"aware:actor_focus_scope:{actor_id}:{focus_scope_id}")


def stable_actor_focus_scope_evidence_id(*, actor_focus_scope_id: UUID, evidence_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_focus_scope_id, evidence_key"""

    evidence_key_norm = (evidence_key or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:actor_focus_scope_evidence:{actor_focus_scope_id}:{evidence_key_norm}")


def stable_actor_focus_scope_request_id(*, actor_focus_scope_id: UUID, focus_scope_request_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_focus_scope_id, focus_scope_request_id"""

    return uuid5(NS_ATTENTION, f"aware:actor_focus_scope_request:{actor_focus_scope_id}:{focus_scope_request_id}")


def stable_attention_focus_transition_id(
    *, attention_session_section_id: UUID, focus_scope_id: UUID, transition_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_session_section_id, focus_scope_id, transition_key"""

    transition_key_norm = (transition_key or "").casefold().strip()
    return uuid5(
        NS_ATTENTION,
        f"aware:attention_focus_transition:{attention_session_section_id}:{focus_scope_id}:{transition_key_norm}",
    )


def stable_attention_layout_topology_transition_id(*, attention_session_layout_id: UUID, client_intent_id: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_session_layout_id, client_intent_id"""

    client_intent_id_norm = (client_intent_id or "").casefold().strip()
    return uuid5(
        NS_ATTENTION,
        f"aware:attention_layout_topology_transition:{attention_session_layout_id}:{client_intent_id_norm}",
    )


def stable_attention_layout_topology_transition_section_id(
    *, attention_layout_topology_transition_id: UUID, attention_session_section_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_layout_topology_transition_id, attention_session_section_id"""

    return uuid5(
        NS_ATTENTION,
        f"aware:attention_layout_topology_transition_section:{attention_layout_topology_transition_id}:{attention_session_section_id}",
    )


def stable_attention_layout_transition_id(*, attention_session_layout_id: UUID, client_intent_id: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_session_layout_id, client_intent_id"""

    client_intent_id_norm = (client_intent_id or "").casefold().strip()
    return uuid5(
        NS_ATTENTION, f"aware:attention_layout_transition:{attention_session_layout_id}:{client_intent_id_norm}"
    )


def stable_attention_layout_transition_section_id(
    *, attention_layout_transition_id: UUID, attention_session_section_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_layout_transition_id, attention_session_section_id"""

    return uuid5(
        NS_ATTENTION,
        f"aware:attention_layout_transition_section:{attention_layout_transition_id}:{attention_session_section_id}",
    )


def stable_attention_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:attention_package:{name_norm}")


def stable_attention_package_layout_config_id(*, attention_package_id: UUID, layout_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_package_id, layout_config_id"""

    return uuid5(NS_ATTENTION, f"aware:attention_package_layout_config:{attention_package_id}:{layout_config_id}")


def stable_attention_session_id(*, identity_session_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_session_id"""

    return uuid5(NS_ATTENTION, f"aware:attention_session:{identity_session_id}")


def stable_attention_session_layout_id(*, attention_session_id: UUID, layout_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_session_id, layout_id"""

    return uuid5(NS_ATTENTION, f"aware:attention_session_layout:{attention_session_id}:{layout_id}")


def stable_attention_session_section_id(
    *, attention_session_layout_id: UUID, layout_section_id: UUID, section_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: attention_session_layout_id, layout_section_id, section_id"""

    return uuid5(
        NS_ATTENTION, f"aware:attention_session_section:{attention_session_layout_id}:{layout_section_id}:{section_id}"
    )


def stable_focus_id(*, object_projection_graph_identity_id: UUID, focus_scope_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_projection_graph_identity_id, focus_scope_id"""

    return uuid5(NS_ATTENTION, f"aware:focus:{object_projection_graph_identity_id}:{focus_scope_id}")


def stable_focus_scope_id(*, title: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: title"""

    title_norm = (title or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:focus_scope:{title_norm}")


def stable_focus_scope_commit_id(
    *, focus_scope_id: UUID, focus_id: UUID, object_instance_graph_commit_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: focus_scope_id, focus_id, object_instance_graph_commit_id"""

    return uuid5(
        NS_ATTENTION, f"aware:focus_scope_commit:{focus_scope_id}:{focus_id}:{object_instance_graph_commit_id}"
    )


def stable_focus_scope_request_id(*, focus_scope_id: UUID, focus_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: focus_scope_id, focus_id"""

    return uuid5(NS_ATTENTION, f"aware:focus_scope_request:{focus_scope_id}:{focus_id}")


def stable_focus_scope_request_response_id(*, focus_scope_request_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: focus_scope_request_id"""

    return uuid5(NS_ATTENTION, f"aware:focus_scope_request_response:{focus_scope_request_id}")


def stable_layout_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:layout:{key_norm}")


def stable_layout_config_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:layout_config:{key_norm}")


def stable_layout_config_section_config_id(*, layout_config_id: UUID, section_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: layout_config_id, section_key"""

    section_key_norm = (section_key or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:layout_config_section_config:{layout_config_id}:{section_key_norm}")


def stable_layout_section_id(*, layout_id: UUID, section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: layout_id, section_id"""

    return uuid5(NS_ATTENTION, f"aware:layout_section:{layout_id}:{section_id}")


def stable_section_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:section:{key_norm}")


def stable_section_config_id(*, layout_config_section_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: layout_config_section_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ATTENTION, f"aware:section_config:{layout_config_section_config_id}:{key_norm}")


def stable_section_focus_scope_id(*, section_id: UUID, focus_scope_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: section_id, focus_scope_id"""

    return uuid5(NS_ATTENTION, f"aware:section_focus_scope:{section_id}:{focus_scope_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "02e3ccd4-9a17-5887-9c25-d13efa820d82": (
        "stable_attention_layout_transition_section_id",
        ("attention_layout_transition_id", "attention_session_section_id"),
    ),
    "07cf95b1-0068-56e2-b737-d03129fce2ca": ("stable_actor_focus_scope_id", ("actor_id", "focus_scope_id")),
    "1ca0c28b-8c76-5952-9046-dca1d1d3e568": ("stable_section_focus_scope_id", ("section_id", "focus_scope_id")),
    "1fdb9c8a-960d-5793-a127-4d5ff806118e": ("stable_section_config_id", ("layout_config_section_config_id", "key")),
    "20bd4e9a-3762-5af6-9d64-d17f07aa6ee7": ("stable_actor_focus_evidence_id", ("actor_focus_id", "evidence_key")),
    "2259ca7e-57a0-574c-ad70-6c1ec92a08e6": (
        "stable_actor_focus_scope_request_id",
        ("actor_focus_scope_id", "focus_scope_request_id"),
    ),
    "3012da7d-5f8e-5c0d-9020-a002a56647ba": (
        "stable_attention_session_section_id",
        ("attention_session_layout_id", "layout_section_id", "section_id"),
    ),
    "3e874dd1-fb93-58c0-a217-2a58019d43d4": (
        "stable_attention_layout_transition_id",
        ("attention_session_layout_id", "client_intent_id"),
    ),
    "4afbf582-ab2f-57b3-bb41-2259618d08b6": ("stable_actor_focus_id", ("actor_id", "focus_id")),
    "72776555-365b-5a0e-94ae-29d99b310dfc": ("stable_layout_id", ("key",)),
    "775535ff-49e9-53a0-96a9-120ccb8b0afd": (
        "stable_attention_layout_topology_transition_section_id",
        ("attention_layout_topology_transition_id", "attention_session_section_id"),
    ),
    "7f01ff0c-0a9a-50ea-8213-82b0d9e8e554": ("stable_focus_scope_request_response_id", ("focus_scope_request_id",)),
    "81c0fbe2-0577-5cf0-b540-c85daee42aca": (
        "stable_actor_focus_scope_evidence_id",
        ("actor_focus_scope_id", "evidence_key"),
    ),
    "83b14ad9-8af0-57f0-bfcd-e1e7166b3522": ("stable_attention_session_id", ("identity_session_id",)),
    "8e57a110-39b3-52f1-a6df-da3ce9229e23": (
        "stable_attention_session_layout_id",
        ("attention_session_id", "layout_id"),
    ),
    "9f9afbf1-e6c2-5ce5-83d1-a4063d3b9248": (
        "stable_attention_package_layout_config_id",
        ("attention_package_id", "layout_config_id"),
    ),
    "b6db0813-e6fe-57a9-b477-7be9243a8ef0": ("stable_section_id", ("key",)),
    "bcfaa41b-0c1d-57a8-9f43-cde6e9f2850c": (
        "stable_focus_scope_commit_id",
        ("focus_scope_id", "focus_id", "object_instance_graph_commit_id"),
    ),
    "be6a26c7-7d4e-5f23-8f7e-d182d44c4acd": ("stable_layout_section_id", ("layout_id", "section_id")),
    "c467a156-20bd-5d1a-b635-07caef3975a7": ("stable_layout_config_id", ("key",)),
    "d00e09a2-d2a3-5559-93d1-54193e96b7ae": (
        "stable_layout_config_section_config_id",
        ("layout_config_id", "section_key"),
    ),
    "d20765ff-a73b-59c3-8af8-42e43299c664": (
        "stable_attention_layout_topology_transition_id",
        ("attention_session_layout_id", "client_intent_id"),
    ),
    "dcabb070-9acc-54f9-86e2-b777c2a55aaf": (
        "stable_focus_id",
        ("object_projection_graph_identity_id", "focus_scope_id"),
    ),
    "f0a45d58-3334-5acc-8601-89259f50d36a": (
        "stable_attention_focus_transition_id",
        ("attention_session_section_id", "focus_scope_id", "transition_key"),
    ),
    "f67ccc0a-9480-5fe8-a4a4-07c3d1149c16": ("stable_attention_package_id", ("name",)),
    "fe93f9c6-0b4a-5132-bdde-f15c2a4a75b0": ("stable_focus_scope_request_id", ("focus_scope_id", "focus_id")),
}

__all__ = [
    "stable_actor_focus_id",
    "stable_actor_focus_evidence_id",
    "stable_actor_focus_request_id",
    "stable_actor_focus_request_response_id",
    "stable_actor_focus_scope_id",
    "stable_actor_focus_scope_evidence_id",
    "stable_actor_focus_scope_request_id",
    "stable_attention_focus_transition_id",
    "stable_attention_layout_topology_transition_id",
    "stable_attention_layout_topology_transition_section_id",
    "stable_attention_layout_transition_id",
    "stable_attention_layout_transition_section_id",
    "stable_attention_package_id",
    "stable_attention_package_layout_config_id",
    "stable_attention_session_id",
    "stable_attention_session_layout_id",
    "stable_attention_session_section_id",
    "stable_focus_id",
    "stable_focus_scope_id",
    "stable_focus_scope_commit_id",
    "stable_focus_scope_request_id",
    "stable_focus_scope_request_response_id",
    "stable_layout_id",
    "stable_layout_config_id",
    "stable_layout_config_section_config_id",
    "stable_layout_section_id",
    "stable_section_id",
    "stable_section_config_id",
    "stable_section_focus_scope_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
