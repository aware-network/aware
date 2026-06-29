# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_ONTOLOGY = uuid5(NAMESPACE_URL, "aware://ontology/v1")


def stable_ontology_id(*, ontology_config_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: ontology_config_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_ONTOLOGY, f"aware:ontology:{ontology_config_id}:{key_norm}")


def stable_ontology_config_id(*, fqn_prefix: str, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, name"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ONTOLOGY, f"aware:ontology_config:{fqn_prefix_norm}:{name_norm}")


def stable_ontology_package_id(*, fqn_prefix: str, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: fqn_prefix, name"""

    fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ONTOLOGY, f"aware:ontology_package:{fqn_prefix_norm}:{name_norm}")


def stable_ontology_package_dependency_id(*, ontology_package_id: UUID, target_ontology_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: ontology_package_id, target_ontology_package_id"""

    return uuid5(NS_ONTOLOGY, f"aware:ontology_package_dependency:{ontology_package_id}:{target_ontology_package_id}")


def stable_ontology_package_runtime_code_package_id(*, ontology_package_id: UUID, code_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: ontology_package_id, code_package_id"""

    return uuid5(NS_ONTOLOGY, f"aware:ontology_package_runtime_code_package:{ontology_package_id}:{code_package_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "043af7f1-9107-5933-b6cb-fcc86f658424": ("stable_ontology_id", ("ontology_config_id", "key")),
    "0b865742-53d4-5022-a869-f9d322547c21": (
        "stable_ontology_package_dependency_id",
        ("ontology_package_id", "target_ontology_package_id"),
    ),
    "6f05623c-8965-5768-85ba-03a41d8b9803": (
        "stable_ontology_package_runtime_code_package_id",
        ("ontology_package_id", "code_package_id"),
    ),
    "bead5bba-40ce-5bef-8e0e-200caf0615b0": ("stable_ontology_config_id", ("fqn_prefix", "name")),
    "d76251eb-85fe-56fb-8eea-154d30f22e5b": ("stable_ontology_package_id", ("fqn_prefix", "name")),
}

__all__ = [
    "stable_ontology_id",
    "stable_ontology_config_id",
    "stable_ontology_package_id",
    "stable_ontology_package_dependency_id",
    "stable_ontology_package_runtime_code_package_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
