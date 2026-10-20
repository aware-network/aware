"""Read-only first-Goal preparation over the original Project/source owners.

This is not a committed Goal reading or creation permission. Domain laws stay
in neutral Goal Runtime; Workspace authenticates source facts; Project owns its
selected content. Publication and membership remain separate unenabled effects.
"""

from __future__ import annotations

import json
import os
from weakref import WeakKeyDictionary

from aware_goal_operational_runtime.planning_creation_request import (
    PlanningGoalCreationRequestV2,
)
from aware_goal_operational_runtime.planning_intent_document import (
    validate_planning_goal_creator,
)
from aware_workspace_sdk.initial_authoring.goal_source import InitialGoalSourceContext

from .project_create_contract import canonical, reference
from .project_initial_source import _workspace, show_initial_project

_PREPARATIONS = WeakKeyDictionary()
_PINS = WeakKeyDictionary()


def _body(request, facts, project_reading):
    # Facts come only from Workspace's original nominal context. This pure
    # consistency call does not authenticate the supplied correlation itself.
    creator = validate_planning_goal_creator(
        request,
        {
            "kind": "provider_execution_correlation",
            "execution_id": facts["execution_id"],
            "evidence_ref": facts["enrollment_ref"],
        },
    )
    source = project_reading["source"]
    if (
        source["revision"] != facts["source_revision"]
        or source["path"] != facts["project_path"]
        or source["blob_oid"] != facts["project_blob_oid"]
        or source["manifest_sha256"] != facts["manifest_sha256"]
        or source["publication_ref"] != facts["project_publication_ref"]
        or source["projection_ref"] != facts["project_projection_ref"]
        or project_reading["caller"]["execution_id"] != facts["execution_id"]
    ):
        raise ValueError("planning_goal_project_source_mismatch")
    body = {
        "schema_id": "aware.goal.planning-source-preparation.v1",
        "request": request.to_wire(),
        "source_context": facts,
        "project_reading": project_reading,
        "creator_binding": creator,
        "planning_state": "not_yet_decomposed",
        "creation_permission": "not_issued",
    }
    return {
        **body,
        "preparation_ref": reference("goal-planning-source-preparation", body),
    }


class GoalPlanningSourcePreparation:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use prepare_initial_planning_goal_source")

    def __copy__(self):
        raise TypeError("planning_goal_preparation_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("planning_goal_preparation_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("planning_goal_preparation_not_serializable")

    def to_wire(self):
        value = (
            _PREPARATIONS.get(self)
            if type(self) is GoalPlanningSourcePreparation
            else None
        )
        pins = _PINS.get(self) if type(self) is GoalPlanningSourcePreparation else None
        if value is None or pins is None or value != pins or value[0] != os.getpid():
            raise ValueError("planning_goal_preparation_not_issued_or_mutated")
        _, workspace, capability, project_request, request, context, sealed = value
        _workspace(workspace)
        if type(context) is not InitialGoalSourceContext:
            raise ValueError("original_initial_goal_context_required")
        facts = context.require_current()
        reading = show_initial_project(
            workspace=workspace,
            resolver_capability=capability,
            publication_request=project_request,
        )
        current = _body(request, facts, reading.to_wire())
        # The provider must recheck HEAD after qualified Project reading too;
        # that reader/its terminal resolution can observe concurrent movement.
        if canonical(context.require_current()) != canonical(facts):
            raise ValueError("planning_goal_source_changed")
        if canonical(current) != sealed:
            raise ValueError("planning_goal_preparation_changed")
        return json.loads(sealed)

    def require_current(self):
        return self.to_wire()


def prepare_initial_planning_goal_source(
    *,
    workspace,
    resolver_capability,
    project_publication_request,
    target_path,
    request: PlanningGoalCreationRequestV2,
):
    """Observe qualified inputs only; no durable attempt, permission or writer."""
    if type(request) is not PlanningGoalCreationRequestV2:
        raise ValueError("exact_planning_goal_request_required")
    request.to_wire()
    _workspace(workspace)
    reading = show_initial_project(
        workspace=workspace,
        resolver_capability=resolver_capability,
        publication_request=project_publication_request,
    )
    context = workspace.observe_initial_goal_source(
        project_publication_request,
        resolver_capability=resolver_capability,
        target_path=target_path,
    )
    body = _body(request, context.require_current(), reading.to_wire())
    preparation = object.__new__(GoalPlanningSourcePreparation)
    state = (
        os.getpid(),
        workspace,
        resolver_capability,
        project_publication_request,
        request,
        context,
        canonical(body),
    )
    _PREPARATIONS[preparation] = state
    _PINS[preparation] = state
    preparation.require_current()
    return preparation
