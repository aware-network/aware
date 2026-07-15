# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_ENVIRONMENT = uuid5(NAMESPACE_URL, "aware://environment/v1")


def stable_environment_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment:{key_norm}")


def stable_environment_config_id(*, handle: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: handle"""

    handle_norm = (handle or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_config:{handle_norm}")


def stable_environment_config_ontology_config_id(*, environment_config_id: UUID, fqn_prefix: str, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_config_id, fqn_prefix, name"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_ENVIRONMENT,
        f"aware:environment_config_ontology_config:{environment_config_id}:{fqn_prefix_norm}:{name_norm}",
    )


def stable_environment_config_package_id(*, handle: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: handle"""

    handle_norm = (handle or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_config_package:{handle_norm}")


def stable_environment_config_package_dependency_id(
    *,
    environment_config_package_id: UUID,
    target_environment_config_package_id: UUID,
    target_environment_config_package_object_instance_graph_commit_id: UUID,
    dependency_role: str,
    dependency_index: int,
    target_handle: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_config_package_id, target_environment_config_package_id, target_environment_config_package_object_instance_graph_commit_id, dependency_role, dependency_index, target_handle"""

    dependency_role_norm = (dependency_role or "").casefold().strip()
    target_handle_norm = (target_handle or "").casefold().strip()
    return uuid5(
        NS_ENVIRONMENT,
        f"aware:environment_config_package_dependency:{environment_config_package_id}:{target_environment_config_package_id}:{target_environment_config_package_object_instance_graph_commit_id}:{dependency_role_norm}:{dependency_index}:{target_handle_norm}",
    )


def stable_environment_config_package_ontology_package_id(
    *, environment_config_package_id: UUID, fqn_prefix: str, name: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_config_package_id, fqn_prefix, name"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_ENVIRONMENT,
        f"aware:environment_config_package_ontology_package:{environment_config_package_id}:{fqn_prefix_norm}:{name_norm}",
    )


def stable_environment_navigation_context_id(*, environment_session_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_session_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_navigation_context:{environment_session_id}:{key_norm}")


def stable_environment_ontology_id(*, environment_id: UUID, ontology_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_id, ontology_id"""

    return uuid5(NS_ENVIRONMENT, f"aware:environment_ontology:{environment_id}:{ontology_id}")


def stable_environment_profile_id(*, environment_id: UUID, profile_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_id, profile_config_id"""

    return uuid5(NS_ENVIRONMENT, f"aware:environment_profile:{environment_id}:{profile_config_id}")


def stable_environment_profile_actor_config_id(
    *, environment_profile_config_id: UUID, actor_config_id: UUID, policy_key: str = "admit"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_profile_config_id, actor_config_id, policy_key"""

    policy_key_norm = (policy_key or "").casefold().strip() or "admit"
    return uuid5(
        NS_ENVIRONMENT,
        f"aware:environment_profile_actor_config:{environment_profile_config_id}:{actor_config_id}:{policy_key_norm}",
    )


def stable_environment_profile_config_id(*, environment_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_profile_config:{environment_config_id}:{key_norm}")


def stable_environment_profile_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_profile_package:{name_norm}")


def stable_environment_profile_package_dependency_id(
    *, environment_profile_package_id: UUID, target_environment_profile_package_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_profile_package_id, target_environment_profile_package_id"""

    return uuid5(
        NS_ENVIRONMENT,
        f"aware:environment_profile_package_dependency:{environment_profile_package_id}:{target_environment_profile_package_id}",
    )


def stable_environment_provider_id(*, environment_profile_config_id: UUID, provider_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_profile_config_id, provider_key"""

    provider_key_norm = (provider_key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_provider:{environment_profile_config_id}:{provider_key_norm}")


def stable_environment_provider_grant_id(*, environment_provider_id: UUID, grant_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_provider_id, grant_key"""

    grant_key_norm = (grant_key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_provider_grant:{environment_provider_id}:{grant_key_norm}")


def stable_environment_session_id(*, environment_id: UUID, identity_session_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_id, identity_session_id"""

    return uuid5(NS_ENVIRONMENT, f"aware:environment_session:{environment_id}:{identity_session_id}")


def stable_environment_session_attention_session_id(
    *, environment_session_id: UUID, attention_session_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_session_id, attention_session_id"""

    return uuid5(
        NS_ENVIRONMENT, f"aware:environment_session_attention_session:{environment_session_id}:{attention_session_id}"
    )


def stable_environment_session_config_id(*, environment_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:environment_session_config:{environment_config_id}:{key_norm}")


def stable_environment_session_thread_id(
    *, environment_session_id: UUID, thread_id: UUID, thread_layout_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_session_id, thread_id, thread_layout_id"""

    return uuid5(
        NS_ENVIRONMENT, f"aware:environment_session_thread:{environment_session_id}:{thread_id}:{thread_layout_id}"
    )


def stable_process_id(*, environment_profile_id: UUID, process_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_profile_id, process_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:process:{environment_profile_id}:{process_config_id}:{key_norm}")


def stable_process_config_id(*, environment_profile_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: environment_profile_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:process_config:{environment_profile_config_id}:{key_norm}")


def stable_thread_id(*, process_id: UUID, thread_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: process_id, thread_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:thread:{process_id}:{thread_config_id}:{key_norm}")


def stable_thread_config_id(*, process_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: process_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ENVIRONMENT, f"aware:thread_config:{process_config_id}:{key_norm}")


def stable_thread_config_layout_config_id(*, thread_config_id: UUID, layout_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: thread_config_id, layout_config_id"""

    return uuid5(NS_ENVIRONMENT, f"aware:thread_config_layout_config:{thread_config_id}:{layout_config_id}")


def stable_thread_config_layout_config_section_id(
    *, thread_config_layout_config_id: UUID, layout_config_section_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: thread_config_layout_config_id, layout_config_section_config_id"""

    return uuid5(
        NS_ENVIRONMENT,
        f"aware:thread_config_layout_config_section:{thread_config_layout_config_id}:{layout_config_section_config_id}",
    )


def stable_thread_config_object_projection_graph_id(
    *, thread_config_id: UUID, object_projection_graph_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: thread_config_id, object_projection_graph_id"""

    return uuid5(
        NS_ENVIRONMENT, f"aware:thread_config_object_projection_graph:{thread_config_id}:{object_projection_graph_id}"
    )


def stable_thread_layout_id(*, thread_id: UUID, layout_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: thread_id, layout_id"""

    return uuid5(NS_ENVIRONMENT, f"aware:thread_layout:{thread_id}:{layout_id}")


def stable_thread_object_instance_graph_branch_id(*, object_instance_graph_branch_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_branch_id"""

    return uuid5(NS_ENVIRONMENT, f"aware:thread_object_instance_graph_branch:{object_instance_graph_branch_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "0af2a6ed-590d-50e0-ba9c-5162bd3b5b60": ("stable_thread_layout_id", ("thread_id", "layout_id")),
    "0ebb7a68-b081-59c1-983e-67d5bf9759da": (
        "stable_environment_profile_package_dependency_id",
        ("environment_profile_package_id", "target_environment_profile_package_id"),
    ),
    "149873f4-8333-55f6-aca4-72bbafeefb74": (
        "stable_environment_config_package_dependency_id",
        (
            "environment_config_package_id",
            "target_environment_config_package_id",
            "target_environment_config_package_object_instance_graph_commit_id",
            "dependency_role",
            "dependency_index",
            "target_handle",
        ),
    ),
    "1723cd63-cd68-5c1b-b955-e37e9ae2ddd5": ("stable_environment_ontology_id", ("environment_id", "ontology_id")),
    "2fe7b919-1d04-5c55-bfb1-d1795619c012": (
        "stable_thread_config_layout_config_section_id",
        ("thread_config_layout_config_id", "layout_config_section_config_id"),
    ),
    "3d540c24-5098-5291-87fc-28baf831604d": ("stable_thread_config_id", ("process_config_id", "key")),
    "4e254503-55e2-5014-8550-85dee034c2a2": (
        "stable_environment_session_id",
        ("environment_id", "identity_session_id"),
    ),
    "4e688221-3f96-5961-a831-346c38b53606": ("stable_environment_config_id", ("handle",)),
    "5d27245b-86db-56db-9e92-315765499cfb": ("stable_process_config_id", ("environment_profile_config_id", "key")),
    "5d396103-7848-53b9-9bd6-45d53adb0555": ("stable_environment_session_config_id", ("environment_config_id", "key")),
    "6849f7b1-2be3-5d86-8cb3-9c6a9dcd4587": ("stable_environment_config_package_id", ("handle",)),
    "6b7580ff-db9d-5136-9dfe-4b49262ff0a2": (
        "stable_environment_session_attention_session_id",
        ("environment_session_id", "attention_session_id"),
    ),
    "71961d38-6418-53c8-9e4f-bbd0479e9232": (
        "stable_thread_config_object_projection_graph_id",
        ("thread_config_id", "object_projection_graph_id"),
    ),
    "8f5c145f-e150-5947-b119-890d2128b5d8": (
        "stable_environment_provider_id",
        ("environment_profile_config_id", "provider_key"),
    ),
    "985f5910-fc18-5f5f-a9f0-5345c7db22fc": (
        "stable_environment_session_thread_id",
        ("environment_session_id", "thread_id", "thread_layout_id"),
    ),
    "add65104-a5c3-5d73-8a3f-d31aef1b05dc": ("stable_environment_profile_id", ("environment_id", "profile_config_id")),
    "af4dba0e-6a9d-56b5-a26d-d71abed5293a": (
        "stable_process_id",
        ("environment_profile_id", "process_config_id", "key"),
    ),
    "b626aa79-4107-552c-b8af-0ffb36b9fc9a": (
        "stable_environment_config_ontology_config_id",
        ("environment_config_id", "fqn_prefix", "name"),
    ),
    "c0da2eda-797d-54a3-87af-de234c0d9eb7": (
        "stable_environment_provider_grant_id",
        ("environment_provider_id", "grant_key"),
    ),
    "d6ee7547-9d51-5208-af30-24addcfe3218": ("stable_environment_id", ("key",)),
    "db93d31b-9f3c-5090-8094-452b61f7f885": (
        "stable_environment_profile_actor_config_id",
        ("environment_profile_config_id", "actor_config_id", "policy_key"),
    ),
    "dc25f247-856f-5b97-8642-eca85284daa1": ("stable_environment_profile_package_id", ("name",)),
    "e01228c4-bc69-5184-8f05-f2913fb1b2ad": ("stable_environment_profile_config_id", ("environment_config_id", "key")),
    "e0515a91-7fef-5615-8077-7befbca37ff2": (
        "stable_environment_navigation_context_id",
        ("environment_session_id", "key"),
    ),
    "f3e68958-85fc-59fb-ad9a-d439ff669598": (
        "stable_thread_config_layout_config_id",
        ("thread_config_id", "layout_config_id"),
    ),
    "f5874d83-4245-506d-9f12-dbb6af5634a5": (
        "stable_environment_config_package_ontology_package_id",
        ("environment_config_package_id", "fqn_prefix", "name"),
    ),
    "faecade4-a09f-56de-bd36-ae99d40d057c": ("stable_thread_id", ("process_id", "thread_config_id", "key")),
}

__all__ = [
    "stable_environment_id",
    "stable_environment_config_id",
    "stable_environment_config_ontology_config_id",
    "stable_environment_config_package_id",
    "stable_environment_config_package_dependency_id",
    "stable_environment_config_package_ontology_package_id",
    "stable_environment_navigation_context_id",
    "stable_environment_ontology_id",
    "stable_environment_profile_id",
    "stable_environment_profile_actor_config_id",
    "stable_environment_profile_config_id",
    "stable_environment_profile_package_id",
    "stable_environment_profile_package_dependency_id",
    "stable_environment_provider_id",
    "stable_environment_provider_grant_id",
    "stable_environment_session_id",
    "stable_environment_session_attention_session_id",
    "stable_environment_session_config_id",
    "stable_environment_session_thread_id",
    "stable_process_id",
    "stable_process_config_id",
    "stable_thread_id",
    "stable_thread_config_id",
    "stable_thread_config_layout_config_id",
    "stable_thread_config_layout_config_section_id",
    "stable_thread_config_object_projection_graph_id",
    "stable_thread_layout_id",
    "stable_thread_object_instance_graph_branch_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
