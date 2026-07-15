from __future__ import annotations

from uuid import UUID

from aware_history_ontology.stable_ids import stable_branch_id as _stable_branch_id


def normalize_branch_tail(*, tail: str | None) -> str:
    return (tail or "").casefold().strip() or "default"


def resolve_environment_thread_branch_key(
    *,
    environment_id: UUID,
    thread_id: UUID,
    tail: str | None = None,
) -> str:
    tail_norm = normalize_branch_tail(tail=tail)
    return f"env:{environment_id}:thread:{thread_id}:key:{tail_norm}"


def resolve_environment_turn_branch_key(
    *,
    environment_id: UUID,
    turn_id: UUID,
) -> str:
    return f"env:{environment_id}:turn:{turn_id}"


def stable_environment_thread_branch_id(
    *,
    environment_id: UUID,
    thread_id: UUID,
    tail: str | None = None,
) -> UUID:
    return _stable_branch_id(
        key=resolve_environment_thread_branch_key(
            environment_id=environment_id,
            thread_id=thread_id,
            tail=tail,
        )
    )


def stable_environment_turn_branch_id(
    *,
    environment_id: UUID,
    turn_id: UUID,
) -> UUID:
    return _stable_branch_id(
        key=resolve_environment_turn_branch_key(
            environment_id=environment_id,
            turn_id=turn_id,
        )
    )


__all__ = [
    "normalize_branch_tail",
    "resolve_environment_turn_branch_key",
    "resolve_environment_thread_branch_key",
    "stable_environment_turn_branch_id",
    "stable_environment_thread_branch_id",
]
