# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_SDK = uuid5(NAMESPACE_URL, "aware://sdk/v1")


def stable_sdk_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SDK, f"aware:sdk_config:{name_norm}")


def stable_sdk_operation_id(*, sdk_config_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_config_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SDK, f"aware:sdk_operation:{sdk_config_id}:{name_norm}")


def stable_sdk_operation_api_capability_endpoint_id(
    *, sdk_operation_id: UUID, api_capability_endpoint_id: UUID, name: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_operation_id, api_capability_endpoint_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_SDK,
        f"aware:sdk_operation_api_capability_endpoint:{sdk_operation_id}:{api_capability_endpoint_id}:{name_norm}",
    )


def stable_sdk_operation_call_id(*, sdk_operation_id: UUID, call_key: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_operation_id, call_key"""

    return uuid5(NS_SDK, f"aware:sdk_operation_call:{sdk_operation_id}:{call_key}")


def stable_sdk_operation_dependency_id(*, sdk_operation_id: UUID, target_sdk_operation_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_operation_id, target_sdk_operation_id"""

    return uuid5(NS_SDK, f"aware:sdk_operation_dependency:{sdk_operation_id}:{target_sdk_operation_id}")


def stable_sdk_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SDK, f"aware:sdk_package:{name_norm}")


def stable_sdk_package_api_package_id(*, sdk_package_id: UUID, api_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_package_id, api_package_id"""

    return uuid5(NS_SDK, f"aware:sdk_package_api_package:{sdk_package_id}:{api_package_id}")


def stable_sdk_package_dependency_id(*, sdk_package_id: UUID, target_sdk_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_package_id, target_sdk_package_id"""

    return uuid5(NS_SDK, f"aware:sdk_package_dependency:{sdk_package_id}:{target_sdk_package_id}")


def stable_sdk_package_implementation_package_id(*, sdk_package_id: UUID, code_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_package_id, code_package_id"""

    return uuid5(NS_SDK, f"aware:sdk_package_implementation_package:{sdk_package_id}:{code_package_id}")


def stable_sdk_package_object_config_graph_package_id(
    *, sdk_package_id: UUID, object_config_graph_package_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_package_id, object_config_graph_package_id"""

    return uuid5(
        NS_SDK, f"aware:sdk_package_object_config_graph_package:{sdk_package_id}:{object_config_graph_package_id}"
    )


def stable_sdk_surface_id(*, sdk_config_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_config_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SDK, f"aware:sdk_surface:{sdk_config_id}:{name_norm}")


def stable_sdk_surface_method_id(*, sdk_surface_id: UUID, target_sdk_operation_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: sdk_surface_id, target_sdk_operation_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SDK, f"aware:sdk_surface_method:{sdk_surface_id}:{target_sdk_operation_id}:{name_norm}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "146f1646-6a3d-58ab-96b9-7ffa3667ca3b": ("stable_sdk_config_id", ("name",)),
    "157c5c91-4bfd-50d6-8541-3307e2f11cb4": ("stable_sdk_operation_call_id", ("sdk_operation_id", "call_key")),
    "26b1b986-3ece-54d5-ad7b-5d50436a38b2": ("stable_sdk_operation_id", ("sdk_config_id", "name")),
    "38c2d232-24ca-5d8a-b0e6-02023f9eb88c": (
        "stable_sdk_package_implementation_package_id",
        ("sdk_package_id", "code_package_id"),
    ),
    "393837f2-331c-5068-80ec-b7dabde71b75": (
        "stable_sdk_operation_api_capability_endpoint_id",
        ("sdk_operation_id", "api_capability_endpoint_id", "name"),
    ),
    "8c1aaa28-8aa8-5530-8e54-4209a6a67a71": ("stable_sdk_package_id", ("name",)),
    "8d2242d6-e2e0-59fa-b4b2-e70894d4c6ce": (
        "stable_sdk_package_dependency_id",
        ("sdk_package_id", "target_sdk_package_id"),
    ),
    "a09c72bf-fcda-5317-8550-aca8ec000ab8": ("stable_sdk_package_api_package_id", ("sdk_package_id", "api_package_id")),
    "a828776e-f2f7-5982-8797-1d9c59abb857": ("stable_sdk_surface_id", ("sdk_config_id", "name")),
    "ce242d31-16cd-5493-86f9-2fba0f873932": (
        "stable_sdk_surface_method_id",
        ("sdk_surface_id", "target_sdk_operation_id", "name"),
    ),
    "f8e16ae4-b241-5e8f-93d0-1298a9b22ecf": (
        "stable_sdk_operation_dependency_id",
        ("sdk_operation_id", "target_sdk_operation_id"),
    ),
    "fb4700b5-da13-5947-b9fc-af5e2b582aa3": (
        "stable_sdk_package_object_config_graph_package_id",
        ("sdk_package_id", "object_config_graph_package_id"),
    ),
}

__all__ = [
    "stable_sdk_config_id",
    "stable_sdk_operation_id",
    "stable_sdk_operation_api_capability_endpoint_id",
    "stable_sdk_operation_call_id",
    "stable_sdk_operation_dependency_id",
    "stable_sdk_package_id",
    "stable_sdk_package_api_package_id",
    "stable_sdk_package_dependency_id",
    "stable_sdk_package_implementation_package_id",
    "stable_sdk_package_object_config_graph_package_id",
    "stable_sdk_surface_id",
    "stable_sdk_surface_method_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
