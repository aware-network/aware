from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.actor.actor_focus_enums import ActorFocusLevelType
from aware_attention_ontology.actor.actor_focus_request import ActorFocusRequest
from aware_attention_ontology.actor.actor_focus_request_response import ActorFocusRequestResponse

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from datetime import timezone
from typing import Any

from aware_attention_ontology.actor.actor_focus_enums import ActorFocusRequestStatus
from aware_meta.runtime.handler_context import current_handler_context


def _request_status(value: object) -> ActorFocusRequestStatus:
    if isinstance(value, ActorFocusRequestStatus):
        return value
    return ActorFocusRequestStatus(getattr(value, "value", value))


def _current_actor_id() -> UUID:
    try:
        context = current_handler_context()
    except RuntimeError as exc:
        raise PermissionError("ActorContext missing: actor_id not set") from exc
    actor_id = _optional_uuid(getattr(context, "requester_id", None))
    if actor_id is None:
        raise PermissionError("ActorContext missing: actor_id not set")
    return actor_id


def _current_branch_id() -> UUID:
    try:
        context = current_handler_context()
    except RuntimeError as exc:
        raise PermissionError("InvocationContext missing: branch_id not set") from exc
    branch_id = _optional_uuid(getattr(context, "branch_id", None))
    if branch_id is None:
        raise PermissionError("InvocationContext missing: branch_id not set")
    return branch_id


def _optional_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


# --- AWARE: USER_IMPORTS END


async def build(
    sender_id: UUID,
    receiver_id: UUID,
    focus_id: UUID,
    suggested_level: ActorFocusLevelType,
    rationale: str,
    confidence: float | None = None,
    expires_at: datetime | None = None,
) -> ActorFocusRequest:
    """
    Builds a new ActorFocusRequest.
    """

    # --- AWARE: LOGIC START build
    return ActorFocusRequest(
        id=_current_branch_id(),
        sender_id=sender_id,
        receiver_id=receiver_id,
        focus_id=focus_id,
        suggested_level=suggested_level,
        rationale=rationale,
        confidence=confidence,
        expires_at=expires_at,
    )
    # --- AWARE: LOGIC END build


async def accept(actor_focus_request: ActorFocusRequest, decided_by_id: UUID) -> ActorFocusRequestResponse:
    """
    Accepts the request if it is pending and has not expired.
    """

    # --- AWARE: LOGIC START accept
    if decided_by_id != _current_actor_id():
        raise PermissionError("decided_by_id must match the current actor")

    receiver_id = getattr(actor_focus_request, "receiver_id", None)
    if receiver_id is None:
        receiver = getattr(actor_focus_request, "receiver", None)
        receiver_id = getattr(receiver, "id", None) if receiver is not None else None

    if receiver_id is not None and decided_by_id != receiver_id:
        raise PermissionError("Only the request receiver can accept the focus request")

    now = datetime.now(timezone.utc)
    expires_at = getattr(actor_focus_request, "expires_at", None)
    if expires_at is not None and getattr(expires_at, "tzinfo", None) is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    status = _request_status(actor_focus_request.status)
    if expires_at is not None and now >= expires_at:
        if status == ActorFocusRequestStatus.pending:
            actor_focus_request.status = ActorFocusRequestStatus.expired
            actor_focus_request.response_message = "Request expired"
        return {
            "key": "default",
            "success": False,
            "message": "This focus request has expired.",
        }

    match status:
        case ActorFocusRequestStatus.accepted:
            return {"key": "default", "success": True, "message": "Already accepted."}
        case ActorFocusRequestStatus.rejected:
            return {
                "key": "default",
                "success": False,
                "message": "This focus request was rejected.",
            }
        case ActorFocusRequestStatus.expired:
            return {
                "key": "default",
                "success": False,
                "message": "This focus request has expired.",
            }
        case ActorFocusRequestStatus.pending:
            pass
        case _:
            raise ValueError(f"Unsupported ActorFocusRequestStatus: {status}")

    actor_focus_request.status = ActorFocusRequestStatus.accepted
    actor_focus_request.response_message = "Accepted"
    return {"key": "default", "success": True, "message": "Accepted."}
    # --- AWARE: LOGIC END accept


async def expire(actor_focus_request: ActorFocusRequest) -> int:
    """
    Expires the request if it has expired.
    """

    # --- AWARE: LOGIC START expire
    status = _request_status(actor_focus_request.status)
    if status != ActorFocusRequestStatus.pending:
        return 0
    now = datetime.now(timezone.utc)
    expires_at = getattr(actor_focus_request, "expires_at", None)
    if expires_at is not None and getattr(expires_at, "tzinfo", None) is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at is None or now < expires_at:
        return 0
    actor_focus_request.status = ActorFocusRequestStatus.expired
    actor_focus_request.response_message = "Request expired"
    return 1
    # --- AWARE: LOGIC END expire


async def reject(actor_focus_request: ActorFocusRequest, decided_by_id: UUID) -> ActorFocusRequestResponse:
    """
    Rejects the request if it is pending and has not expired.
    """

    # --- AWARE: LOGIC START reject
    if decided_by_id != _current_actor_id():
        raise PermissionError("decided_by_id must match the current actor")

    receiver_id = getattr(actor_focus_request, "receiver_id", None)
    if receiver_id is None:
        receiver = getattr(actor_focus_request, "receiver", None)
        receiver_id = getattr(receiver, "id", None) if receiver is not None else None

    if receiver_id is not None and decided_by_id != receiver_id:
        raise PermissionError("Only the request receiver can reject the focus request")

    now = datetime.now(timezone.utc)
    expires_at = getattr(actor_focus_request, "expires_at", None)
    if expires_at is not None and getattr(expires_at, "tzinfo", None) is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    status = _request_status(actor_focus_request.status)
    if expires_at is not None and now >= expires_at:
        if status == ActorFocusRequestStatus.pending:
            actor_focus_request.status = ActorFocusRequestStatus.expired
            actor_focus_request.response_message = "Request expired"
        return {
            "key": "default",
            "success": False,
            "message": "This focus request has expired.",
        }

    match status:
        case ActorFocusRequestStatus.accepted:
            return {
                "key": "default",
                "success": False,
                "message": "This focus request was already accepted.",
            }
        case ActorFocusRequestStatus.rejected:
            return {"key": "default", "success": True, "message": "Already rejected."}
        case ActorFocusRequestStatus.expired:
            return {
                "key": "default",
                "success": False,
                "message": "This focus request has expired.",
            }
        case ActorFocusRequestStatus.pending:
            pass
        case _:
            raise ValueError(f"Unsupported ActorFocusRequestStatus: {status}")

    actor_focus_request.status = ActorFocusRequestStatus.rejected
    actor_focus_request.response_message = "Rejected"
    return {"key": "default", "success": True, "message": "Rejected."}
    # --- AWARE: LOGIC END reject
