from __future__ import annotations

from uuid import UUID, NAMESPACE_URL, uuid4, uuid5


def resolve_program_run_id(
    *,
    environment_id: UUID,
    process_id: UUID | None,
    thread_id: UUID | None,
    target_actor_id: UUID,
    program_ref: str,
    mailbox_key: str,
    idempotency_key: str | None,
) -> UUID:
    """Return Experience-owned program run identity.

    Contract:
    - idempotent requests (`idempotency_key`) map to stable UUID5 identity.
    - non-idempotent requests get fresh UUID4 identity.
    """

    normalized_idempotency_key = str(idempotency_key or "").strip()
    if not normalized_idempotency_key:
        return uuid4()

    normalized_program_ref = str(program_ref or "").strip()
    normalized_mailbox_key = str(mailbox_key or "").strip()
    process_token = str(process_id) if process_id is not None else "none"
    thread_token = str(thread_id) if thread_id is not None else "none"
    stable_name = (
        f"aware:program_run:{environment_id}:{process_token}:{thread_token}:"
        + f"{target_actor_id}:{normalized_program_ref}:{normalized_mailbox_key}:"
        + normalized_idempotency_key
    )
    return uuid5(
        NAMESPACE_URL,
        stable_name,
    )
