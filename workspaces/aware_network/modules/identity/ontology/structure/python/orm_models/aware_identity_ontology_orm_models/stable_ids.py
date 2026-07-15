# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_IDENTITY = uuid5(NAMESPACE_URL, "aware://identity/v1")


def stable_actor_id(*, identity_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_IDENTITY, f"aware:actor:{identity_id}:{key_norm}")


def stable_actor_commit_id(
    *, actor_id: UUID, domain_branch_id: UUID, domain_projection_hash: str, domain_commit_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, domain_branch_id, domain_projection_hash, domain_commit_id"""

    domain_projection_hash_norm = (domain_projection_hash or "").casefold().strip()
    return uuid5(
        NS_IDENTITY,
        f"aware:actor_commit:{actor_id}:{domain_branch_id}:{domain_projection_hash_norm}:{domain_commit_id}",
    )


def stable_actor_config_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:actor_config:{key_norm}")


def stable_actor_config_role_config_id(*, actor_config_id: UUID, role_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_config_id, role_config_id"""

    return uuid5(NS_IDENTITY, f"aware:actor_config_role_config:{actor_config_id}:{role_config_id}")


def stable_actor_event_id(*, actor_id: UUID, event_id: UUID, role: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, event_id, role"""

    role_norm = (role or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:actor_event:{actor_id}:{event_id}:{role_norm}")


def stable_actor_role_id(*, actor_id: UUID, role_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, role_id"""

    return uuid5(NS_IDENTITY, f"aware:actor_role:{actor_id}:{role_id}")


def stable_actor_role_delta_plan_id(*, actor_role_id: UUID, to_role_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_role_id, to_role_config_id"""

    return uuid5(NS_IDENTITY, f"aware:actor_role_delta_plan:{actor_role_id}:{to_role_config_id}")


def stable_actor_subscription_id(*, actor_id: UUID, event_config_condition_config_scope_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id, event_config_condition_config_scope_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_IDENTITY, f"aware:actor_subscription:{actor_id}:{event_config_condition_config_scope_id}:{name_norm}"
    )


def stable_actor_subscription_event_id(
    *, actor_subscription_id: UUID, event_config_condition_config_scope_event_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_subscription_id, event_config_condition_config_scope_event_id"""

    return uuid5(
        NS_IDENTITY,
        f"aware:actor_subscription_event:{actor_subscription_id}:{event_config_condition_config_scope_event_id}",
    )


def stable_auth_token_id(*, auth_token_registry_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: auth_token_registry_id"""

    return uuid5(NS_IDENTITY, f"aware:auth_token:{auth_token_registry_id}")


def stable_auth_token_registry_id(*, key: str = "v1") -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip() or "v1"
    return uuid5(NS_IDENTITY, f"aware:auth_token_registry:{key_norm}")


def stable_credential_grant_id(
    *, credential_profile_id: UUID, grant_key: str, scope_kind: str, scope_value: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: credential_profile_id, grant_key, scope_kind, scope_value"""

    grant_key_norm = (grant_key or "").casefold().strip()
    scope_kind_norm = (scope_kind or "").casefold().strip()
    scope_value_norm = (scope_value or "").casefold().strip()
    return uuid5(
        NS_IDENTITY,
        f"aware:credential_grant:{credential_profile_id}:{grant_key_norm}:{scope_kind_norm}:{scope_value_norm}",
    )


def stable_credential_profile_id(*, identity_id: UUID, profile_key: str, target_kind: str = "aware_api") -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_id, profile_key, target_kind"""

    profile_key_norm = (profile_key or "").casefold().strip()
    target_kind_norm = (target_kind or "").casefold().strip() or "aware_api"
    return uuid5(NS_IDENTITY, f"aware:credential_profile:{identity_id}:{profile_key_norm}:{target_kind_norm}")


def stable_credential_readiness_receipt_id(*, credential_profile_id: UUID, receipt_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: credential_profile_id, receipt_key"""

    receipt_key_norm = (receipt_key or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:credential_readiness_receipt:{credential_profile_id}:{receipt_key_norm}")


def stable_credential_secret_material_ref_id(
    *, credential_profile_id: UUID, secret_ref_key: str, resolver_kind: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: credential_profile_id, secret_ref_key, resolver_kind"""

    secret_ref_key_norm = (secret_ref_key or "").casefold().strip()
    resolver_kind_norm = (resolver_kind or "").casefold().strip()
    return uuid5(
        NS_IDENTITY,
        f"aware:credential_secret_material_ref:{credential_profile_id}:{secret_ref_key_norm}:{resolver_kind_norm}",
    )


def stable_credential_usage_receipt_id(*, credential_profile_id: UUID, receipt_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: credential_profile_id, receipt_key"""

    receipt_key_norm = (receipt_key or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:credential_usage_receipt:{credential_profile_id}:{receipt_key_norm}")


def stable_human_id(*, actor_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id"""

    return uuid5(NS_IDENTITY, f"aware:human:{actor_id}")


def stable_identity_id(*, public_key: str, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: public_key, type"""

    public_key_norm = (public_key or "").casefold().strip()
    type_norm = (type or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:identity:{public_key_norm}:{type_norm}")


def stable_identity_connection_id(
    *, requester_identity_id: UUID, recipient_identity_id: UUID, connection_type: str = "connect"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: requester_identity_id, recipient_identity_id, connection_type"""

    connection_type_norm = (connection_type or "").casefold().strip() or "connect"
    return uuid5(
        NS_IDENTITY, f"aware:identity_connection:{requester_identity_id}:{recipient_identity_id}:{connection_type_norm}"
    )


def stable_identity_pattern_id(*, pattern_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: pattern_key"""

    pattern_key_norm = (pattern_key or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:identity_pattern:{pattern_key_norm}")


def stable_identity_pattern_evidence_id(*, content_part_text_id: UUID, evidence_type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_text_id, evidence_type"""

    evidence_type_norm = (evidence_type or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:identity_pattern_evidence:{content_part_text_id}:{evidence_type_norm}")


def stable_identity_profile_id(*, public_handle: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: public_handle"""

    public_handle_norm = (public_handle or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:identity_profile:{public_handle_norm}")


def stable_organization_id(*, actor_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: actor_id"""

    return uuid5(NS_IDENTITY, f"aware:organization:{actor_id}")


def stable_organization_member_id(*, organization_id: UUID, identity_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: organization_id, identity_id"""

    return uuid5(NS_IDENTITY, f"aware:organization_member:{organization_id}:{identity_id}")


def stable_role_id(
    *, role_config_id: UUID, object_instance_graph_identity_id: UUID, object_instance_graph_branch_key: str = "all"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: role_config_id, object_instance_graph_identity_id, object_instance_graph_branch_key"""

    object_instance_graph_branch_key_norm = (object_instance_graph_branch_key or "").casefold().strip() or "all"
    return uuid5(
        NS_IDENTITY,
        f"aware:role:{role_config_id}:{object_instance_graph_identity_id}:{object_instance_graph_branch_key_norm}",
    )


def stable_role_class_instance_id(
    *, role_id: UUID, class_instance_identity_id: UUID, role_config_class_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: role_id, class_instance_identity_id, role_config_class_config_id"""

    return uuid5(
        NS_IDENTITY, f"aware:role_class_instance:{role_id}:{class_instance_identity_id}:{role_config_class_config_id}"
    )


def stable_role_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:role_config:{name_norm}")


def stable_role_config_class_config_id(*, role_config_id: UUID, class_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: role_config_id, class_config_id"""

    return uuid5(NS_IDENTITY, f"aware:role_config_class_config:{role_config_id}:{class_config_id}")


def stable_role_config_class_config_function_config_id(
    *, role_config_class_config_id: UUID, function_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: role_config_class_config_id, function_config_id"""

    return uuid5(
        NS_IDENTITY,
        f"aware:role_config_class_config_function_config:{role_config_class_config_id}:{function_config_id}",
    )


def stable_role_config_class_config_relationship_id(*, access_level: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: access_level"""

    access_level_norm = (access_level or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:role_config_class_config_relationship:{access_level_norm}")


def stable_session_id(*, session_config_id: UUID, key: str, parent_session_scope_key: str = "root") -> UUID:
    """Compiler-generated from class-attribute identity keys: session_config_id, key, parent_session_scope_key"""

    key_norm = (key or "").casefold().strip()
    parent_session_scope_key_norm = (parent_session_scope_key or "").casefold().strip() or "root"
    return uuid5(NS_IDENTITY, f"aware:session:{session_config_id}:{key_norm}:{parent_session_scope_key_norm}")


def stable_session_config_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:session_config:{key_norm}")


def stable_session_config_actor_config_id(*, session_config_id: UUID, actor_config_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: session_config_id, actor_config_id"""

    return uuid5(NS_IDENTITY, f"aware:session_config_actor_config:{session_config_id}:{actor_config_id}")


def stable_session_member_id(*, session_id: UUID, actor_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: session_id, actor_id"""

    return uuid5(NS_IDENTITY, f"aware:session_member:{session_id}:{actor_id}")


def stable_session_member_actor_role_id(*, session_member_id: UUID, actor_role_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: session_member_id, actor_role_id"""

    return uuid5(NS_IDENTITY, f"aware:session_member_actor_role:{session_member_id}:{actor_role_id}")


def stable_session_provider_id(*, provider_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: provider_key"""

    provider_key_norm = (provider_key or "").casefold().strip()
    return uuid5(NS_IDENTITY, f"aware:session_provider:{provider_key_norm}")


def stable_session_provider_session_id(
    *, session_id: UUID, provider_session_config_id: UUID, provider_session_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: session_id, provider_session_config_id, provider_session_key"""

    provider_session_key_norm = (provider_session_key or "").casefold().strip()
    return uuid5(
        NS_IDENTITY,
        f"aware:session_provider_session:{session_id}:{provider_session_config_id}:{provider_session_key_norm}",
    )


def stable_session_provider_session_config_id(
    *, session_provider_id: UUID, session_config_id: UUID, config_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: session_provider_id, session_config_id, config_key"""

    config_key_norm = (config_key or "").casefold().strip()
    return uuid5(
        NS_IDENTITY,
        f"aware:session_provider_session_config:{session_provider_id}:{session_config_id}:{config_key_norm}",
    )


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "09a7f407-e119-5880-a547-26916e670ac9": ("stable_auth_token_registry_id", ("key",)),
    "0ceb4cd7-02d3-589d-b1cf-edf9e83867c8": (
        "stable_credential_grant_id",
        ("credential_profile_id", "grant_key", "scope_kind", "scope_value"),
    ),
    "11f5ae67-7d75-500a-be98-0d782f051891": ("stable_actor_role_id", ("actor_id", "role_id")),
    "12d71e14-1021-5d90-8e21-05f4bc3a32e8": (
        "stable_session_member_actor_role_id",
        ("session_member_id", "actor_role_id"),
    ),
    "2bef409a-8a41-5685-9837-62359190f274": ("stable_session_provider_id", ("provider_key",)),
    "2c1a1a45-2bb4-5c5b-9d94-814216244842": (
        "stable_role_config_class_config_function_config_id",
        ("role_config_class_config_id", "function_config_id"),
    ),
    "2c4987c7-406c-5016-9294-e0418948e19e": (
        "stable_role_config_class_config_id",
        ("role_config_id", "class_config_id"),
    ),
    "34355ae5-aab2-53a2-bd55-03c75c3580ab": ("stable_identity_profile_id", ("public_handle",)),
    "3b42285b-ab32-5ec1-a6ae-dbb0c9bee06f": (
        "stable_session_provider_session_id",
        ("session_id", "provider_session_config_id", "provider_session_key"),
    ),
    "3cf6d3dc-bd00-5a06-83af-8ad5ff96060f": (
        "stable_session_provider_session_config_id",
        ("session_provider_id", "session_config_id", "config_key"),
    ),
    "3f5a0ec9-acdb-5b91-afd5-dfb84d45fef7": ("stable_actor_config_id", ("key",)),
    "47b1bc7f-b88a-557c-8a14-9cb8b179cc6d": ("stable_identity_id", ("public_key", "type")),
    "529f6cd7-1488-53d7-b44f-47a7f37a74a7": ("stable_actor_id", ("identity_id", "key")),
    "5e3bbd23-f44f-5026-8f87-f408d2d139d7": (
        "stable_actor_config_role_config_id",
        ("actor_config_id", "role_config_id"),
    ),
    "5e8e3a0d-ab75-5136-8e47-054577662d6c": (
        "stable_role_class_instance_id",
        ("role_id", "class_instance_identity_id", "role_config_class_config_id"),
    ),
    "68568b2b-6ec1-5835-8651-769bb62423bb": (
        "stable_role_id",
        ("role_config_id", "object_instance_graph_identity_id", "object_instance_graph_branch_key"),
    ),
    "6fa2a423-0e6b-57fe-bfd6-2e76122c62bc": (
        "stable_actor_commit_id",
        ("actor_id", "domain_branch_id", "domain_projection_hash", "domain_commit_id"),
    ),
    "72c10977-e3f3-5ba4-ad60-347bb0338fdb": (
        "stable_session_id",
        ("session_config_id", "key", "parent_session_scope_key"),
    ),
    "7905b8ae-7c1a-5208-a3ef-cef5b1d910ab": ("stable_session_config_id", ("key",)),
    "7c2fbee5-6f2c-5ab1-b61a-9e87777a6ca6": ("stable_organization_member_id", ("organization_id", "identity_id")),
    "7cb77384-aae8-5ce2-9117-53b62f699509": (
        "stable_credential_profile_id",
        ("identity_id", "profile_key", "target_kind"),
    ),
    "84f4ba3e-450d-5445-bbec-88657d94e27d": ("stable_human_id", ("actor_id",)),
    "8d9b17d5-6e3b-5e27-af5b-09bd47ba4c82": (
        "stable_credential_secret_material_ref_id",
        ("credential_profile_id", "secret_ref_key", "resolver_kind"),
    ),
    "a5a8bb88-e2a6-579e-a79b-76aba2e1f2eb": ("stable_role_config_id", ("name",)),
    "b6b6aac0-89c9-5d3d-98ed-5eee653ddafe": (
        "stable_session_config_actor_config_id",
        ("session_config_id", "actor_config_id"),
    ),
    "c1027737-9124-59a4-84b2-1dfdfad96911": (
        "stable_credential_usage_receipt_id",
        ("credential_profile_id", "receipt_key"),
    ),
    "c19e7768-ee39-57ee-bc9e-758a3283af86": ("stable_auth_token_id", ("auth_token_registry_id",)),
    "c1d064ee-1476-5232-9ae2-ac9ec31a6e12": (
        "stable_actor_subscription_event_id",
        ("actor_subscription_id", "event_config_condition_config_scope_event_id"),
    ),
    "cddd418c-e3fd-5588-86ae-e3f4500cf56a": ("stable_organization_id", ("actor_id",)),
    "d5372157-0bfc-5176-a628-2dfd9c6e4339": (
        "stable_actor_subscription_id",
        ("actor_id", "event_config_condition_config_scope_id", "name"),
    ),
    "da82b87e-c8dc-5cb5-ab83-07dd2e4feb1c": ("stable_session_member_id", ("session_id", "actor_id")),
    "e364845d-5d6a-5ff9-97f3-edda20553f0e": (
        "stable_credential_readiness_receipt_id",
        ("credential_profile_id", "receipt_key"),
    ),
    "f6c2e72b-cde6-5389-935a-d8e6cf3d81ac": (
        "stable_identity_connection_id",
        ("requester_identity_id", "recipient_identity_id", "connection_type"),
    ),
}

__all__ = [
    "stable_actor_id",
    "stable_actor_commit_id",
    "stable_actor_config_id",
    "stable_actor_config_role_config_id",
    "stable_actor_event_id",
    "stable_actor_role_id",
    "stable_actor_role_delta_plan_id",
    "stable_actor_subscription_id",
    "stable_actor_subscription_event_id",
    "stable_auth_token_id",
    "stable_auth_token_registry_id",
    "stable_credential_grant_id",
    "stable_credential_profile_id",
    "stable_credential_readiness_receipt_id",
    "stable_credential_secret_material_ref_id",
    "stable_credential_usage_receipt_id",
    "stable_human_id",
    "stable_identity_id",
    "stable_identity_connection_id",
    "stable_identity_pattern_id",
    "stable_identity_pattern_evidence_id",
    "stable_identity_profile_id",
    "stable_organization_id",
    "stable_organization_member_id",
    "stable_role_id",
    "stable_role_class_instance_id",
    "stable_role_config_id",
    "stable_role_config_class_config_id",
    "stable_role_config_class_config_function_config_id",
    "stable_role_config_class_config_relationship_id",
    "stable_session_id",
    "stable_session_config_id",
    "stable_session_config_actor_config_id",
    "stable_session_member_id",
    "stable_session_member_actor_role_id",
    "stable_session_provider_id",
    "stable_session_provider_session_id",
    "stable_session_provider_session_config_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
