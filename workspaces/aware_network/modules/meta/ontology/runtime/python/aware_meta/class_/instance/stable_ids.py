from __future__ import annotations

from uuid import UUID, uuid5


OIG_STABLE_ID_NAMESPACE = UUID("cba1c7a6-2d8a-4a0f-9a66-7f0c4f7d9d84")


def stable_class_instance_relationship_id(
    *,
    class_config_relationship_id: UUID,
    source_class_instance_id: UUID,
    target_class_instance_id: UUID,
) -> UUID:
    return uuid5(
        OIG_STABLE_ID_NAMESPACE,
        "oig_rel:" f"{class_config_relationship_id}:{source_class_instance_id}:{target_class_instance_id}",
    )


__all__ = [
    "stable_class_instance_relationship_id",
]
