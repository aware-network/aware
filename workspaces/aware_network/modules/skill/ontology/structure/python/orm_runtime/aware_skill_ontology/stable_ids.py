# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_SKILL = uuid5(NAMESPACE_URL, "aware://skill/v1")


def stable_skill_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SKILL, f"aware:skill_config:{name_norm}")


def stable_skill_config_api_id(*, skill_config_id: UUID, api_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_config_id, api_id"""

    return uuid5(NS_SKILL, f"aware:skill_config_api:{skill_config_id}:{api_id}")


def stable_skill_config_api_endpoint_id(
    *, skill_config_api_id: UUID, api_endpoint_id: UUID, capability_name: str, name: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_config_api_id, api_endpoint_id, capability_name, name"""

    capability_name_norm = (capability_name or "").casefold().strip()
    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_SKILL,
        f"aware:skill_config_api_endpoint:{skill_config_api_id}:{api_endpoint_id}:{capability_name_norm}:{name_norm}",
    )


def stable_skill_config_experience_id(*, skill_config_id: UUID, projection_experience_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_config_id, projection_experience_id"""

    return uuid5(NS_SKILL, f"aware:skill_config_experience:{skill_config_id}:{projection_experience_id}")


def stable_skill_config_step_id(*, skill_config_id: UUID, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_config_id, position"""

    return uuid5(NS_SKILL, f"aware:skill_config_step:{skill_config_id}:{position}")


def stable_skill_config_step_target_id(*, skill_config_step_id: UUID, skill_config_target_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_config_step_id, skill_config_target_id"""

    return uuid5(NS_SKILL, f"aware:skill_config_step_target:{skill_config_step_id}:{skill_config_target_id}")


def stable_skill_config_target_id(
    *, skill_config_experience_id: UUID, projection_experience_graph_identity_id: UUID, name: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_config_experience_id, projection_experience_graph_identity_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(
        NS_SKILL,
        f"aware:skill_config_target:{skill_config_experience_id}:{projection_experience_graph_identity_id}:{name_norm}",
    )


def stable_skill_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_SKILL, f"aware:skill_package:{name_norm}")


def stable_skill_package_api_package_id(*, skill_package_id: UUID, api_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_package_id, api_package_id"""

    return uuid5(NS_SKILL, f"aware:skill_package_api_package:{skill_package_id}:{api_package_id}")


def stable_skill_run_id(*, skill_config_id: UUID, run_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_config_id, run_key"""

    run_key_norm = (run_key or "").casefold().strip()
    return uuid5(NS_SKILL, f"aware:skill_run:{skill_config_id}:{run_key_norm}")


def stable_skill_run_step_id(*, skill_run_id: UUID, skill_config_step_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: skill_run_id, skill_config_step_id"""

    return uuid5(NS_SKILL, f"aware:skill_run_step:{skill_run_id}:{skill_config_step_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "0ceb1e1a-eff9-55b9-b175-41c8cad42906": ("stable_skill_package_id", ("name",)),
    "271532d9-225d-5454-9cb4-f69c32dcd453": ("stable_skill_run_step_id", ("skill_run_id", "skill_config_step_id")),
    "7361f5c5-fc8c-5946-9e33-71494d4674ce": (
        "stable_skill_config_api_endpoint_id",
        ("skill_config_api_id", "api_endpoint_id", "capability_name", "name"),
    ),
    "95935813-0208-5ee7-bc56-f5d556dd21b5": ("stable_skill_config_id", ("name",)),
    "b8204a9f-8692-51a9-af3c-b673bc655998": (
        "stable_skill_config_target_id",
        ("skill_config_experience_id", "projection_experience_graph_identity_id", "name"),
    ),
    "bbf1a8cb-8640-5f8e-8934-10f230e958c8": ("stable_skill_config_api_id", ("skill_config_id", "api_id")),
    "c83a0ae1-310c-5b35-8b5c-b751720ba009": (
        "stable_skill_package_api_package_id",
        ("skill_package_id", "api_package_id"),
    ),
    "d1ed9190-6206-5d4f-80e1-7468be80a387": ("stable_skill_config_step_id", ("skill_config_id", "position")),
    "db72dc68-7f8f-5a8f-8fa3-74e206b26970": (
        "stable_skill_config_experience_id",
        ("skill_config_id", "projection_experience_id"),
    ),
    "e5d5510f-1325-58e4-ac09-1711196453aa": ("stable_skill_run_id", ("skill_config_id", "run_key")),
    "f03532c4-be48-59eb-953a-ed21e24cdc2d": (
        "stable_skill_config_step_target_id",
        ("skill_config_step_id", "skill_config_target_id"),
    ),
}

__all__ = [
    "stable_skill_config_id",
    "stable_skill_config_api_id",
    "stable_skill_config_api_endpoint_id",
    "stable_skill_config_experience_id",
    "stable_skill_config_step_id",
    "stable_skill_config_step_target_id",
    "stable_skill_config_target_id",
    "stable_skill_package_id",
    "stable_skill_package_api_package_id",
    "stable_skill_run_id",
    "stable_skill_run_step_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
