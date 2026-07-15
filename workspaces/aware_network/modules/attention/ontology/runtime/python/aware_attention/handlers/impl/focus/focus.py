from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.focus.focus import Focus

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_context,
)

# --- AWARE: USER_IMPORTS END


async def build(
    focus_scope_id: UUID,
    object_projection_graph_identity_id: UUID,
    projection_hash: str | None = None,
    object_instance_graph_branch_id: UUID | None = None,
    target_type: str | None = None,
    target_id: UUID | None = None,
    description: str | None = None,
    expires_at: datetime | None = None,
    is_active: bool = True,
    last_accessed: datetime | None = None,
) -> Focus:
    """
    Builds a new Focus.
    """

    # --- AWARE: LOGIC START build
    ctx = current_handler_context()
    if ctx.branch_id is None:
        raise RuntimeError("Focus.build requires HandlerContext.branch_id")
    return Focus(
        id=ctx.branch_id,
        focus_scope_id=focus_scope_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        projection_hash=projection_hash,
        target_type=target_type,
        target_id=target_id,
        description=description,
        expires_at=expires_at,
        is_active=is_active,
        last_accessed=last_accessed,
    )
    # --- AWARE: LOGIC END build
