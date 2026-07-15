# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_types import canonical_decimal_text

NS_SERVICE = uuid5(NAMESPACE_URL, "aware://service/v1")


def stable_service_id(*, service_config_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_config_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SERVICE, f"aware:service:{service_config_id}:{name_norm}")


def stable_service_api_provider_set_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_SERVICE, f"aware:service_api_provider_set:{key_norm}")


def stable_service_api_provider_set_service_package_id(
    *, service_api_provider_set_id: UUID, service_package_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_api_provider_set_id, service_package_id"""

    return uuid5(
        NS_SERVICE, f"aware:service_api_provider_set_service_package:{service_api_provider_set_id}:{service_package_id}"
    )


def stable_service_branch_id(
    *, service_id: UUID, service_config_api_projection_id: UUID, object_instance_graph_branch_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_id, service_config_api_projection_id, object_instance_graph_branch_id"""

    return uuid5(
        NS_SERVICE,
        f"aware:service_branch:{service_id}:{service_config_api_projection_id}:{object_instance_graph_branch_id}",
    )


def stable_service_commercial_profile_id(*, service_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_id"""

    return uuid5(NS_SERVICE, f"aware:service_commercial_profile:{service_id}")


def stable_service_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SERVICE, f"aware:service_config:{name_norm}")


def stable_service_config_api_id(*, service_config_id: UUID, api_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_config_id, api_id"""

    return uuid5(NS_SERVICE, f"aware:service_config_api:{service_config_id}:{api_id}")


def stable_service_config_api_projection_id(*, service_config_api_id: UUID, api_graph_projection_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_config_api_id, api_graph_projection_id"""

    return uuid5(NS_SERVICE, f"aware:service_config_api_projection:{service_config_api_id}:{api_graph_projection_id}")


def stable_service_config_code_package_config_id(
    *, service_config_id: UUID, code_package_config_id: UUID, slot_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_config_id, code_package_config_id, slot_key"""

    slot_key_norm = (slot_key or "").casefold().strip()
    return uuid5(
        NS_SERVICE,
        f"aware:service_config_code_package_config:{service_config_id}:{code_package_config_id}:{slot_key_norm}",
    )


def stable_service_config_experience_id(*, service_config_id: UUID, projection_experience_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_config_id, projection_experience_id"""

    return uuid5(NS_SERVICE, f"aware:service_config_experience:{service_config_id}:{projection_experience_id}")


def stable_service_contract_id(*, service_id: UUID, service_contract_config_id: UUID, smart_contract_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_id, service_contract_config_id, smart_contract_id"""

    return uuid5(NS_SERVICE, f"aware:service_contract:{service_id}:{service_contract_config_id}:{smart_contract_id}")


def stable_service_contract_config_id(*, service_config_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_config_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SERVICE, f"aware:service_contract_config:{service_config_id}:{name_norm}")


def stable_service_contract_config_actor_role_grant_id(
    *, service_contract_config_id: UUID, role_config_id: UUID, scope_kind: str = "service", scope_ref: str = "default"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_contract_config_id, role_config_id, scope_kind, scope_ref"""

    scope_kind_norm = (scope_kind or "").casefold().strip() or "service"
    scope_ref_norm = (scope_ref or "").casefold().strip() or "default"
    return uuid5(
        NS_SERVICE,
        f"aware:service_contract_config_actor_role_grant:{service_contract_config_id}:{role_config_id}:{scope_kind_norm}:{scope_ref_norm}",
    )


def stable_service_contract_config_operation_grant_id(
    *, service_contract_config_id: UUID, service_operation_config_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_contract_config_id, service_operation_config_id"""

    return uuid5(
        NS_SERVICE,
        f"aware:service_contract_config_operation_grant:{service_contract_config_id}:{service_operation_config_id}",
    )


def stable_service_contract_economy_settlement_id(*, service_contract_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_contract_id"""

    return uuid5(NS_SERVICE, f"aware:service_contract_economy_settlement:{service_contract_id}")


def stable_service_contract_operation_permit_policy_id(*, service_contract_config_operation_grant_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_contract_config_operation_grant_id"""

    return uuid5(
        NS_SERVICE, f"aware:service_contract_operation_permit_policy:{service_contract_config_operation_grant_id}"
    )


def stable_service_contract_operation_price_policy_id(*, service_contract_config_operation_grant_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_contract_config_operation_grant_id"""

    return uuid5(
        NS_SERVICE, f"aware:service_contract_operation_price_policy:{service_contract_config_operation_grant_id}"
    )


def stable_service_contract_operation_quota_policy_id(*, service_contract_config_operation_grant_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_contract_config_operation_grant_id"""

    return uuid5(
        NS_SERVICE, f"aware:service_contract_operation_quota_policy:{service_contract_config_operation_grant_id}"
    )


def stable_service_operation_id(*, service_id: UUID, service_operation_config_id: UUID, operation_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_id, service_operation_config_id, operation_key"""

    operation_key_norm = (operation_key or "").casefold().strip()
    return uuid5(NS_SERVICE, f"aware:service_operation:{service_id}:{service_operation_config_id}:{operation_key_norm}")


def stable_service_operation_config_id(*, service_config_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_config_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SERVICE, f"aware:service_operation_config:{service_config_id}:{name_norm}")


def stable_service_operation_config_api_endpoint_id(
    *, service_operation_config_id: UUID, api_capability_endpoint_id: UUID, service_config_api_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_operation_config_id, api_capability_endpoint_id, service_config_api_id"""

    return uuid5(
        NS_SERVICE,
        f"aware:service_operation_config_api_endpoint:{service_operation_config_id}:{api_capability_endpoint_id}:{service_config_api_id}",
    )


def stable_service_operation_config_api_endpoint_function_id(
    *, service_operation_config_api_endpoint_id: UUID, api_capability_endpoint_function_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_operation_config_api_endpoint_id, api_capability_endpoint_function_id"""

    return uuid5(
        NS_SERVICE,
        f"aware:service_operation_config_api_endpoint_function:{service_operation_config_api_endpoint_id}:{api_capability_endpoint_function_id}",
    )


def stable_service_operation_config_api_view_id(
    *, service_operation_config_id: UUID, api_view_id: UUID, service_config_api_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_operation_config_id, api_view_id, service_config_api_id"""

    return uuid5(
        NS_SERVICE,
        f"aware:service_operation_config_api_view:{service_operation_config_id}:{api_view_id}:{service_config_api_id}",
    )


def stable_service_operation_config_role_requirement_id(
    *,
    service_operation_config_id: UUID,
    role_config_id: UUID,
    access_scope: str = "operation",
    scope_kind: str = "operation",
    scope_ref: str = "default",
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_operation_config_id, role_config_id, access_scope, scope_kind, scope_ref"""

    access_scope_norm = (access_scope or "").casefold().strip() or "operation"
    scope_kind_norm = (scope_kind or "").casefold().strip() or "operation"
    scope_ref_norm = (scope_ref or "").casefold().strip() or "default"
    return uuid5(
        NS_SERVICE,
        f"aware:service_operation_config_role_requirement:{service_operation_config_id}:{role_config_id}:{access_scope_norm}:{scope_kind_norm}:{scope_ref_norm}",
    )


def stable_service_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SERVICE, f"aware:service_package:{name_norm}")


def stable_service_package_implementation_package_id(*, service_package_id: UUID, code_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_package_id, code_package_id"""

    return uuid5(NS_SERVICE, f"aware:service_package_implementation_package:{service_package_id}:{code_package_id}")


def stable_service_package_object_config_graph_package_id(
    *, service_package_id: UUID, object_config_graph_package_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_package_id, object_config_graph_package_id"""

    return uuid5(
        NS_SERVICE,
        f"aware:service_package_object_config_graph_package:{service_package_id}:{object_config_graph_package_id}",
    )


def stable_service_package_ontology_package_id(*, service_package_id: UUID, ontology_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_package_id, ontology_package_id"""

    return uuid5(NS_SERVICE, f"aware:service_package_ontology_package:{service_package_id}:{ontology_package_id}")


def stable_service_package_provided_api_package_id(*, service_package_id: UUID, api_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_package_id, api_package_id"""

    return uuid5(NS_SERVICE, f"aware:service_package_provided_api_package:{service_package_id}:{api_package_id}")


def stable_service_package_required_api_package_id(*, service_package_id: UUID, api_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_package_id, api_package_id"""

    return uuid5(NS_SERVICE, f"aware:service_package_required_api_package:{service_package_id}:{api_package_id}")


def stable_service_plan_id(
    *, service_id: UUID, coin_id: UUID, smart_contract_config_id: UUID, cycle: str, price_amount: Decimal
) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_id, coin_id, smart_contract_config_id, cycle, price_amount"""

    cycle_norm = (cycle or "").casefold().strip()
    price_amount_text = canonical_decimal_text(price_amount)
    return uuid5(
        NS_SERVICE,
        f"aware:service_plan:{service_id}:{coin_id}:{smart_contract_config_id}:{cycle_norm}:{price_amount_text}",
    )


def stable_service_subscription_id(*, consumer_finance_entity_id: UUID, service_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: consumer_finance_entity_id, service_id"""

    return uuid5(NS_SERVICE, f"aware:service_subscription:{consumer_finance_entity_id}:{service_id}")


def stable_service_subscription_cycle_id(*, service_subscription_id: UUID, cycle_number: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_subscription_id, cycle_number"""

    return uuid5(NS_SERVICE, f"aware:service_subscription_cycle:{service_subscription_id}:{cycle_number}")


def stable_service_subscription_invoice_id(*, service_subscription_id: UUID, coin_id: UUID, amount: Decimal) -> UUID:
    """Compiler-generated from class-attribute identity keys: service_subscription_id, coin_id, amount"""

    amount_text = canonical_decimal_text(amount)
    return uuid5(NS_SERVICE, f"aware:service_subscription_invoice:{service_subscription_id}:{coin_id}:{amount_text}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "05f24a0a-746e-5032-a9ef-18f215ff4766": (
        "stable_service_plan_id",
        ("service_id", "coin_id", "smart_contract_config_id", "cycle", "price_amount"),
    ),
    "1f86db91-8d59-58c4-ab1f-8c326aa60b88": (
        "stable_service_config_experience_id",
        ("service_config_id", "projection_experience_id"),
    ),
    "1f9af380-0610-53fb-87e3-755c9426c195": ("stable_service_contract_config_id", ("service_config_id", "name")),
    "25c5ff2c-d5ed-52dc-b10d-4ef9384dda39": (
        "stable_service_contract_id",
        ("service_id", "service_contract_config_id", "smart_contract_id"),
    ),
    "27e0538b-636c-5718-85c8-98a6435cb1cf": (
        "stable_service_package_object_config_graph_package_id",
        ("service_package_id", "object_config_graph_package_id"),
    ),
    "35156ee3-671a-553d-a156-86891d53d242": (
        "stable_service_contract_config_operation_grant_id",
        ("service_contract_config_id", "service_operation_config_id"),
    ),
    "370d4ebd-e46e-52dc-ad44-d75ec8e9d7d6": (
        "stable_service_package_provided_api_package_id",
        ("service_package_id", "api_package_id"),
    ),
    "37a8b576-9ade-5cc3-9a1d-e358b906271c": (
        "stable_service_operation_config_role_requirement_id",
        ("service_operation_config_id", "role_config_id", "access_scope", "scope_kind", "scope_ref"),
    ),
    "3bccdcf0-e105-5f63-b94b-3e6ec2b9a83d": ("stable_service_config_api_id", ("service_config_id", "api_id")),
    "40094f3c-5227-57e2-9e2f-eee14ca994c3": (
        "stable_service_api_provider_set_service_package_id",
        ("service_api_provider_set_id", "service_package_id"),
    ),
    "4598478b-a14e-5359-bbfa-e737dc1388b4": (
        "stable_service_package_ontology_package_id",
        ("service_package_id", "ontology_package_id"),
    ),
    "4f9a334c-1fc0-522d-9e62-3295cd1d9c54": (
        "stable_service_subscription_id",
        ("consumer_finance_entity_id", "service_id"),
    ),
    "66e03069-264a-5b04-80e7-862c194abdbb": (
        "stable_service_operation_config_api_endpoint_id",
        ("service_operation_config_id", "api_capability_endpoint_id", "service_config_api_id"),
    ),
    "6b88f322-100a-58b4-b6bc-2a3d43175898": ("stable_service_commercial_profile_id", ("service_id",)),
    "6d829192-3b13-5c96-a587-a19020576706": (
        "stable_service_contract_config_actor_role_grant_id",
        ("service_contract_config_id", "role_config_id", "scope_kind", "scope_ref"),
    ),
    "7277c449-aed1-5873-838a-42a5be49c086": (
        "stable_service_subscription_invoice_id",
        ("service_subscription_id", "coin_id", "amount"),
    ),
    "7436a347-a191-515d-8ab0-bd9a85fcf2f4": (
        "stable_service_operation_config_api_endpoint_function_id",
        ("service_operation_config_api_endpoint_id", "api_capability_endpoint_function_id"),
    ),
    "7ddaf950-df4e-5eeb-b34a-660988593764": (
        "stable_service_branch_id",
        ("service_id", "service_config_api_projection_id", "object_instance_graph_branch_id"),
    ),
    "809fa55e-058d-525b-a79c-46eba8fd9483": ("stable_service_contract_economy_settlement_id", ("service_contract_id",)),
    "812f2d57-db86-5729-b4c2-f8e153265a78": ("stable_service_config_id", ("name",)),
    "8f80f12a-16a5-5932-9958-38a697903c2c": ("stable_service_package_id", ("name",)),
    "98dec89d-3657-5f91-bd48-e154e463f1f8": ("stable_service_api_provider_set_id", ("key",)),
    "a666126d-24c5-5eba-8636-6c9c2b43914a": (
        "stable_service_config_code_package_config_id",
        ("service_config_id", "code_package_config_id", "slot_key"),
    ),
    "aa9a79ec-ea9e-51a6-a272-4380a41b86c4": (
        "stable_service_operation_config_api_view_id",
        ("service_operation_config_id", "api_view_id", "service_config_api_id"),
    ),
    "ac3feff5-f1f3-51cf-9684-2b8a27468371": (
        "stable_service_package_required_api_package_id",
        ("service_package_id", "api_package_id"),
    ),
    "bf49d62b-61e1-5a37-993e-f941076c0717": (
        "stable_service_config_api_projection_id",
        ("service_config_api_id", "api_graph_projection_id"),
    ),
    "c16b6cec-5fa0-59f6-9ed0-e42273a20f2c": (
        "stable_service_subscription_cycle_id",
        ("service_subscription_id", "cycle_number"),
    ),
    "d772b07a-e154-5f64-b68f-9b3b63df2cd4": (
        "stable_service_contract_operation_quota_policy_id",
        ("service_contract_config_operation_grant_id",),
    ),
    "da0be204-4f84-5f13-8cef-fc18ed4feffe": ("stable_service_operation_config_id", ("service_config_id", "name")),
    "dfd50e02-8155-5666-aca0-0b6612b275e4": (
        "stable_service_contract_operation_price_policy_id",
        ("service_contract_config_operation_grant_id",),
    ),
    "e7274877-03b2-5d39-8aa4-4d6e653f9036": (
        "stable_service_operation_id",
        ("service_id", "service_operation_config_id", "operation_key"),
    ),
    "e94d9f0a-f0ee-5e02-a830-18a49827fc75": (
        "stable_service_package_implementation_package_id",
        ("service_package_id", "code_package_id"),
    ),
    "fd1b12ed-e33d-5091-9b4b-ca311cd5ca31": (
        "stable_service_contract_operation_permit_policy_id",
        ("service_contract_config_operation_grant_id",),
    ),
    "fe2f61e9-571f-58b7-8b35-689abf9f296a": ("stable_service_id", ("service_config_id", "name")),
}

__all__ = [
    "stable_service_id",
    "stable_service_api_provider_set_id",
    "stable_service_api_provider_set_service_package_id",
    "stable_service_branch_id",
    "stable_service_commercial_profile_id",
    "stable_service_config_id",
    "stable_service_config_api_id",
    "stable_service_config_api_projection_id",
    "stable_service_config_code_package_config_id",
    "stable_service_config_experience_id",
    "stable_service_contract_id",
    "stable_service_contract_config_id",
    "stable_service_contract_config_actor_role_grant_id",
    "stable_service_contract_config_operation_grant_id",
    "stable_service_contract_economy_settlement_id",
    "stable_service_contract_operation_permit_policy_id",
    "stable_service_contract_operation_price_policy_id",
    "stable_service_contract_operation_quota_policy_id",
    "stable_service_operation_id",
    "stable_service_operation_config_id",
    "stable_service_operation_config_api_endpoint_id",
    "stable_service_operation_config_api_endpoint_function_id",
    "stable_service_operation_config_api_view_id",
    "stable_service_operation_config_role_requirement_id",
    "stable_service_package_id",
    "stable_service_package_implementation_package_id",
    "stable_service_package_object_config_graph_package_id",
    "stable_service_package_ontology_package_id",
    "stable_service_package_provided_api_package_id",
    "stable_service_package_required_api_package_id",
    "stable_service_plan_id",
    "stable_service_subscription_id",
    "stable_service_subscription_cycle_id",
    "stable_service_subscription_invoice_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
