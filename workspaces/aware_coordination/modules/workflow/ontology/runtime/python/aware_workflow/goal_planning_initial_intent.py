"""Goal-owned explicit initiation over the original Workspace source/provider.

This call is separate from read-only preparation. No Goal carrier or mutation
is made; the original intent permission is not exact publication admission.
"""

from __future__ import annotations

from .goal_planning_initial_source import (
    _PREPARATIONS,
    GoalPlanningSourcePreparation,
)
from .project_create_contract import canonical


def authorize_initial_planning_goal_intent(preparation):
    if type(preparation) is not GoalPlanningSourcePreparation:
        raise ValueError("original_planning_goal_preparation_required")
    wire = preparation.require_current()
    retained = _PREPARATIONS.get(preparation)
    if retained is None:
        raise ValueError("original_planning_goal_preparation_required")
    _, workspace, _, _, request, context, _ = retained
    if canonical(request.to_wire()) != canonical(wire["request"]):
        raise ValueError("planning_goal_preparation_changed")
    permission = workspace.authorize_initial_goal_intent(
        context,
        intent_payload=canonical(wire["request"]),
        idempotency_key=request.to_wire()["idempotency_key"],
    )
    # Retain no alternative verifier or permission cache. Every later consumer
    # must ask the original live permission to qualify source/retention again.
    current = permission.require_current()
    if canonical(current["source"]) != canonical(wire["source_context"]) or current[
        "intent_utf8"
    ].encode("utf-8") != canonical(request.to_wire()):
        raise ValueError("planning_goal_intent_permission_mismatch")
    preparation.require_current()
    return permission
