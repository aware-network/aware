from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.focus.focus_scope_request import FocusScopeRequest
from aware_attention_ontology.focus.focus_scope_request_response import FocusScopeRequestResponse

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.focus.focus_enums import FocusScopeRequestStatus
from aware_attention_ontology.stable_ids import stable_focus_scope_request_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def accept(
    focus_scope_request: FocusScopeRequest, decided_by_id: UUID, message: str | None = None
) -> FocusScopeRequestResponse:
    """
    Accepts the request if it is pending and has not expired.
    """

    # --- AWARE: LOGIC START accept
    _ = decided_by_id
    if focus_scope_request.state != FocusScopeRequestStatus.pending:
        raise ValueError("FocusScopeRequest is not pending")
    focus_scope_request.state = FocusScopeRequestStatus.accepted
    return await FocusScopeRequestResponse.build_via_focus_scope_request(
        focus_scope_request_id=focus_scope_request.id,
        success=True,
        message=message,
    )
    # --- AWARE: LOGIC END accept


async def expire(focus_scope_request: FocusScopeRequest) -> int:
    """
    Expires the request if it has expired.
    """

    # --- AWARE: LOGIC START expire
    if focus_scope_request.state != FocusScopeRequestStatus.pending:
        raise ValueError("FocusScopeRequest is not pending")
    focus_scope_request.state = FocusScopeRequestStatus.expired
    return 1
    # --- AWARE: LOGIC END expire


async def reject(
    focus_scope_request: FocusScopeRequest, decided_by_id: UUID, message: str | None = None
) -> FocusScopeRequestResponse:
    """
    Rejects the request if it is pending and has not expired.
    """

    # --- AWARE: LOGIC START reject
    _ = decided_by_id
    if focus_scope_request.state != FocusScopeRequestStatus.pending:
        return await FocusScopeRequestResponse.build_via_focus_scope_request(
            focus_scope_request_id=focus_scope_request.id,
            success=False,
            message=f"FocusScopeRequest is not pending: {focus_scope_request.state}",
        )
    focus_scope_request.state = FocusScopeRequestStatus.rejected
    return await FocusScopeRequestResponse.build_via_focus_scope_request(
        focus_scope_request_id=focus_scope_request.id,
        success=True,
        message=message,
    )
    # --- AWARE: LOGIC END reject


async def create_via_focus_scope(
    focus_scope_id: UUID, focus_id: UUID, rationale: str | None = None
) -> FocusScopeRequest:
    """
    Builds a new FocusScopeRequest
    """

    # --- AWARE: LOGIC START create_via_focus_scope
    return await create_via_focus_scope(
        focus_scope_id=focus_scope_id,
        focus_id=focus_id,
        rationale=rationale,
    )
    # --- AWARE: LOGIC END create_via_focus_scope
