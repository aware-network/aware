from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5


def derive_experience_reference_branch_id(
    *, base_branch_id: UUID, experience_name: str
) -> UUID:
    normalized_name = (experience_name or "").strip().casefold()
    if not normalized_name:
        raise RuntimeError("Experience reference branch requires experience_name")
    return uuid5(
        NAMESPACE_URL,
        f"aware:experience:reference:{base_branch_id}:{normalized_name}",
    )


__all__ = ["derive_experience_reference_branch_id"]
