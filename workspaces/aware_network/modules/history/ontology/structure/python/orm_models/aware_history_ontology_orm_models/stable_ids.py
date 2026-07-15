# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_HISTORY = uuid5(NAMESPACE_URL, "aware://history/v1")


def stable_branch_id(*, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_HISTORY, f"aware:branch:{key_norm}")


def stable_change_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_HISTORY, f"aware:change:{key_norm}")


def stable_change_delta_id(*, change_id: UUID, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: change_id, position"""

    return uuid5(NS_HISTORY, f"aware:change_delta:{change_id}:{position}")


def stable_commit_id(*, lane_id: UUID, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: lane_id, key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_HISTORY, f"aware:commit:{lane_id}:{key_norm}")


def stable_commit_parent_id(*, commit_id: UUID, parent_commit_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: commit_id, parent_commit_id"""

    return uuid5(NS_HISTORY, f"aware:commit_parent:{commit_id}:{parent_commit_id}")


def stable_lane_id(*, branch_id: UUID, lane_hash: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: branch_id, lane_hash"""

    lane_hash_norm = (lane_hash or "").casefold().strip()
    return uuid5(NS_HISTORY, f"aware:lane:{branch_id}:{lane_hash_norm}")


def stable_migration_id(*, version_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: version_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_HISTORY, f"aware:migration:{version_id}:{name_norm}")


def stable_version_id(*, branch_id: UUID, version_number: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: branch_id, version_number"""

    return uuid5(NS_HISTORY, f"aware:version:{branch_id}:{version_number}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "01af5be3-7da4-5303-bcb2-20f6751ca879": ("stable_commit_id", ("lane_id", "key")),
    "23dcf35c-8f94-5e4f-832d-a367a61aa3d4": ("stable_commit_parent_id", ("commit_id", "parent_commit_id")),
    "763370ab-b44f-5269-8df8-231531b293d8": ("stable_version_id", ("branch_id", "version_number")),
    "98e38a0c-9140-514d-8359-9364124e108a": ("stable_change_delta_id", ("change_id", "position")),
    "caafb6e4-eead-528b-9f14-697a9f6b4751": ("stable_lane_id", ("branch_id", "lane_hash")),
    "d340fc06-56e4-5aff-b43d-7a39f2caa11a": ("stable_migration_id", ("version_id", "name")),
    "d97967be-b972-58f6-a5bc-4369809201e0": ("stable_change_id", ("key",)),
    "e36537cd-48ae-5626-8ae7-f11bdfd88778": ("stable_branch_id", ("key",)),
}

__all__ = [
    "stable_branch_id",
    "stable_change_id",
    "stable_change_delta_id",
    "stable_commit_id",
    "stable_commit_parent_id",
    "stable_lane_id",
    "stable_migration_id",
    "stable_version_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
