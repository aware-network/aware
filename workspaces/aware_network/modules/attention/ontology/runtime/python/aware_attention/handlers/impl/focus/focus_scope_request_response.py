from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.focus.focus_scope_request_response import FocusScopeRequestResponse

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_focus_scope_request_response_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_focus_scope_request(
    focus_scope_request_id: UUID, success: bool, message: str | None = None
) -> FocusScopeRequestResponse:
    """
    Builds a new FocusScopeRequestResponse
    """

    # --- AWARE: LOGIC START build_via_focus_scope_request
    return await build_via_focus_scope_request(
        focus_scope_request_id=focus_scope_request_id,
        success=success,
        message=message,
    )
    # --- AWARE: LOGIC END build_via_focus_scope_request
