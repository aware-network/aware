from __future__ import annotations

from uuid import UUID


META_SYSTEM_ACTOR_ID = UUID(int=0)
SYSTEM_ACTOR_ID = META_SYSTEM_ACTOR_ID


def resolve_meta_author_id(value: object) -> UUID:
    """Resolve the author id used for Meta-owned commits."""

    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return META_SYSTEM_ACTOR_ID


def resolve_author_id(value: object) -> UUID:
    """Compatibility name for Meta handlers using the local author facade."""

    return resolve_meta_author_id(value)


__all__ = [
    "META_SYSTEM_ACTOR_ID",
    "SYSTEM_ACTOR_ID",
    "resolve_author_id",
    "resolve_meta_author_id",
]
