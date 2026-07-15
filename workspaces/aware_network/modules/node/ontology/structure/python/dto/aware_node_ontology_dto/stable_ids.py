# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_NODE = uuid5(NAMESPACE_URL, "aware://node/v1")


def stable_node_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_NODE, f"aware:node_config:{name_norm}")


def stable_node_config_environment_profile_mount_id(*, node_config_environment_target_id: UUID, mount_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: node_config_environment_target_id, mount_key"""

    mount_key_norm = (mount_key or "").casefold().strip()
    return uuid5(
        NS_NODE, f"aware:node_config_environment_profile_mount:{node_config_environment_target_id}:{mount_key_norm}"
    )


def stable_node_config_environment_target_id(*, node_config_id: UUID, environment_handle: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: node_config_id, environment_handle"""

    environment_handle_norm = (environment_handle or "").casefold().strip()
    return uuid5(NS_NODE, f"aware:node_config_environment_target:{node_config_id}:{environment_handle_norm}")


def stable_node_config_interface_target_id(*, node_config_id: UUID, interface_name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: node_config_id, interface_name"""

    interface_name_norm = (interface_name or "").casefold().strip()
    return uuid5(NS_NODE, f"aware:node_config_interface_target:{node_config_id}:{interface_name_norm}")


def stable_node_config_ontology_target_id(*, node_config_id: UUID, package_name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: node_config_id, package_name"""

    package_name_norm = (package_name or "").casefold().strip()
    return uuid5(NS_NODE, f"aware:node_config_ontology_target:{node_config_id}:{package_name_norm}")


def stable_node_config_service_code_package_id(
    *, node_config_service_target_id: UUID, slot_key: str, package_name: str, language: str = "aware"
) -> UUID:
    """Compiler-generated from class-attribute identity keys: node_config_service_target_id, slot_key, package_name, language"""

    slot_key_norm = (slot_key or "").casefold().strip()
    package_name_norm = (package_name or "").casefold().strip()
    language_norm = (language or "").casefold().strip() or "aware"
    return uuid5(
        NS_NODE,
        f"aware:node_config_service_code_package:{node_config_service_target_id}:{slot_key_norm}:{package_name_norm}:{language_norm}",
    )


def stable_node_config_service_target_id(*, node_config_id: UUID, service_name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: node_config_id, service_name"""

    service_name_norm = (service_name or "").casefold().strip()
    return uuid5(NS_NODE, f"aware:node_config_service_target:{node_config_id}:{service_name_norm}")


def stable_node_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_NODE, f"aware:node_package:{name_norm}")


def stable_node_package_included_node_package_id(*, node_package_id: UUID, included_package_name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: node_package_id, included_package_name"""

    included_package_name_norm = (included_package_name or "").casefold().strip()
    return uuid5(NS_NODE, f"aware:node_package_included_node_package:{node_package_id}:{included_package_name_norm}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "1fe770a6-67d9-5853-bfe6-5967d1387138": (
        "stable_node_config_interface_target_id",
        ("node_config_id", "interface_name"),
    ),
    "3945e9f9-ec8e-59b9-9e79-b7b000601cb1": ("stable_node_package_id", ("name",)),
    "3c98aed8-be55-51e3-969a-04ca83d64747": (
        "stable_node_package_included_node_package_id",
        ("node_package_id", "included_package_name"),
    ),
    "462d8dc5-ec87-549a-bd71-e0863d9733c0": (
        "stable_node_config_environment_target_id",
        ("node_config_id", "environment_handle"),
    ),
    "9c0f05df-ce97-5de0-80cf-8ae079752067": (
        "stable_node_config_service_code_package_id",
        ("node_config_service_target_id", "slot_key", "package_name", "language"),
    ),
    "af444d6a-2782-555e-8c47-973cf8db9db8": (
        "stable_node_config_environment_profile_mount_id",
        ("node_config_environment_target_id", "mount_key"),
    ),
    "b36b8763-690f-5735-b29e-f271e419e51e": ("stable_node_config_id", ("name",)),
    "c8ba5bcb-14bd-5e3c-a545-ba24af124fba": (
        "stable_node_config_ontology_target_id",
        ("node_config_id", "package_name"),
    ),
    "c982671a-05b3-54de-9341-a77c9e6ada40": (
        "stable_node_config_service_target_id",
        ("node_config_id", "service_name"),
    ),
}

__all__ = [
    "stable_node_config_id",
    "stable_node_config_environment_profile_mount_id",
    "stable_node_config_environment_target_id",
    "stable_node_config_interface_target_id",
    "stable_node_config_ontology_target_id",
    "stable_node_config_service_code_package_id",
    "stable_node_config_service_target_id",
    "stable_node_package_id",
    "stable_node_package_included_node_package_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
