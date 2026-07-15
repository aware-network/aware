from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.focus.focus_scope import FocusScope
from aware_attention_ontology.focus.focus_scope_commit import FocusScopeCommit
from aware_attention_ontology.focus.focus_scope_request import FocusScopeRequest

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_context,
)

# --- AWARE: USER_IMPORTS END


async def build(
    title: str,
    description: str | None = None,
    expires_at: datetime | None = None,
    is_active: bool = True,
    last_accessed: datetime | None = None,
) -> FocusScope:
    """
    Builds a new FocusScope.
    """

    # --- AWARE: LOGIC START build
    ctx = current_handler_context()
    if ctx.branch_id is None:
        raise RuntimeError("FocusScope.build requires HandlerContext.branch_id")
    return FocusScope(
        id=ctx.branch_id,
        title=title,
        description=description,
        expires_at=expires_at,
        is_active=is_active,
        last_accessed=last_accessed,
    )
    # --- AWARE: LOGIC END build


async def create_request(focus_scope: FocusScope, focus_id: UUID, rationale: str | None = None) -> FocusScopeRequest:
    """
    Creates a new FocusScopeRequest.
    """

    # --- AWARE: LOGIC START create_request
    request = await FocusScopeRequest.create_via_focus_scope(
        focus_scope_id=focus_scope.id,
        focus_id=focus_id,
        rationale=rationale,
    )
    if all(existing.id != request.id for existing in focus_scope.requests):
        focus_scope.requests.append(request)
    return request
    # --- AWARE: LOGIC END create_request


async def set_focus(focus_scope: FocusScope, focus_id: UUID, rationale: str | None = None) -> FocusScope:
    """
    Sets the current focus for this scope (commit-backed).
    """

    # --- AWARE: LOGIC START set_focus
    if focus_scope.focus_id == focus_id:
        return focus_scope

    focus_scope.focus_id = focus_id
    focus_scope.rationale = rationale
    return focus_scope
    # --- AWARE: LOGIC END set_focus


async def set_observable(focus_scope: FocusScope, observable_id: UUID, rationale: str | None = None) -> FocusScope:
    """
    Sets the current observable for this scope (commit-backed).
    """

    # --- AWARE: LOGIC START set_observable
    if focus_scope.observable_id == observable_id:
        return focus_scope

    focus_scope.observable_id = observable_id
    focus_scope.rationale = rationale
    return focus_scope
    # --- AWARE: LOGIC END set_observable


async def ensure_commit(
    focus_scope: FocusScope, focus_id: UUID, object_instance_graph_commit_id: UUID
) -> FocusScopeCommit:
    """
    Pin one existing Meta OIG commit under this FocusScope context.

    Canonical v0:
    - `focus_id` is mandatory so consumers can replay the attention context.
    - `object_instance_graph_commit_id` points to Meta-owned commit truth.
    - The FocusScopeCommit create commit time is the observed time; no
      separate `observed_at` scalar is modeled in v0.
    """

    # --- AWARE: LOGIC START ensure_commit
    focus_scope_commit = await FocusScopeCommit.create_via_focus_scope(
        focus_scope_id=focus_scope.id,
        focus_id=focus_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    if all(existing.id != focus_scope_commit.id for existing in focus_scope.commits):
        focus_scope.commits.append(focus_scope_commit)
    return focus_scope_commit
    # --- AWARE: LOGIC END ensure_commit
