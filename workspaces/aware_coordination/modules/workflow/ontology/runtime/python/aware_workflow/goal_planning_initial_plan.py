"""Exact carrier preparation from original live permission; no publication.

The neutral plan is data. This original-owner retained composition requalifies
permission and source, but grants no exact-postimage admission or writer effect.
"""

from __future__ import annotations

import json
import os
from weakref import WeakKeyDictionary

from aware_goal_operational_runtime.planning_initial_plan import (
    decode_goal_planning_initial_plan,
    make_goal_planning_initial_plan,
)
from aware_workspace_sdk.initial_authoring.goal_intent import (
    InitialGoalIntentPermission,
)
from aware_workspace_sdk.initial_authoring.goal_intent import (
    _state as _permission_state,
)

from .goal_planning_initial_source import _PREPARATIONS, GoalPlanningSourcePreparation
from .project_create_contract import canonical, reference
from .project_initial_source import _workspace

_PLANS = WeakKeyDictionary()
_PINS = WeakKeyDictionary()


def _current(preparation, permission):
    if (
        type(preparation) is not GoalPlanningSourcePreparation
        or type(permission) is not InitialGoalIntentPermission
    ):
        raise ValueError("original_planning_source_and_live_intent_permission_required")
    wire = preparation.require_current()
    retained = _PREPARATIONS.get(preparation)
    if retained is None:
        raise ValueError("original_planning_goal_preparation_required")
    _, workspace, _, _, request, _, _ = retained
    owner = _workspace(workspace)
    state = _permission_state(permission)
    if state.owner is not owner:
        raise ValueError("planning_intent_permission_owner_mismatch")
    issued = permission.require_current()
    if (
        canonical(issued["source"]) != canonical(wire["source_context"])
        or issued["intent_utf8"].encode("utf-8") != canonical(wire["request"])
        or issued["idempotency_key"] != wire["request"]["idempotency_key"]
        or issued["publication_admission"] != "not_issued"
    ):
        raise ValueError("planning_intent_permission_request_or_source_mismatch")
    plan = make_goal_planning_initial_plan(
        request,
        creator_binding=wire["creator_binding"],
        source_context_ref=wire["source_context"]["source_ref"],
        intent_permission_ref=issued["permission_ref"],
    )
    body = {
        "schema_id": "aware.goal.planning-postimage-preparation.v1",
        "plan": plan.to_wire(),
        "source_context": wire["source_context"],
        "target_path": wire["source_context"]["target_path"],
        "intent_permission_ref": issued["permission_ref"],
        "publication_admission": "not_issued",
    }
    if canonical(preparation.require_current()) != canonical(wire):
        raise ValueError("planning_postimage_source_changed")
    if canonical(permission.require_current()) != canonical(issued):
        raise ValueError("planning_postimage_permission_changed")
    # Pure final revalidation follows terminal provider I/O. Never repair a
    # caller's original request after concurrent/post-construction mutation.
    if canonical(request.to_wire()) != canonical(wire["request"]):
        raise ValueError("planning_postimage_request_changed")
    return plan, {
        **body,
        "preparation_ref": reference("goal-planning-postimage-preparation", body),
    }


class GoalPlanningPostimagePreparation:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use prepare_initial_planning_goal_postimage")

    def __copy__(self):
        raise TypeError("planning_postimage_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("planning_postimage_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("planning_postimage_not_serializable")

    def to_wire(self):
        retained = (
            _PLANS.get(self) if type(self) is GoalPlanningPostimagePreparation else None
        )
        pins = (
            _PINS.get(self) if type(self) is GoalPlanningPostimagePreparation else None
        )
        if (
            retained is None
            or pins is None
            or retained != pins
            or retained[0] != os.getpid()
        ):
            raise ValueError("planning_postimage_not_issued_or_mutated")
        _, preparation, permission, original, original_body, sealed = retained
        if original.canonical_body != original_body:
            raise ValueError("planning_postimage_plan_mutated")
        plan, current = _current(preparation, permission)
        if plan.canonical_body != original_body or canonical(current) != sealed:
            raise ValueError("planning_postimage_changed")
        return json.loads(sealed)

    def require_current(self):
        return self.to_wire()

    def _workspace_goal_publication_input(self, owner):
        """Original Goal composition supplies exact bytes, not decoded authority."""
        wire = self.require_current()
        retained = _PLANS[self]
        preparation, permission = retained[1:3]
        original = _PREPARATIONS[preparation]
        if _workspace(original[1]) is not owner:
            raise ValueError("planning_postimage_workspace_owner_mismatch")
        source_state = _permission_state(permission)
        from aware_workspace_sdk.initial_authoring.goal_source import _state

        project_request = _state(source_state.context).project_request
        context = wire["source_context"]
        body = {
            "schema_id": "aware.workspace.initial-goal-postimage-source.v1",
            "context": context,
            "project_request": project_request.to_wire(),
            # The complete original join was requalified above. This historical
            # read adds no I/O or new permission and must match its pinned ref.
            "intent_permission": permission.to_wire(),
            "goal_plan": wire["plan"],
            "repository_root": context["repository_root"],
            "execution_id": context["execution_id"],
            "target_path": context["target_path"],
            "expected_head": context["source_revision"],
            "parent_preimages": context["parent_preimages"],
            "content_utf8": wire["plan"]["carrier_utf8"],
            "content_sha256": wire["plan"]["carrier_sha256"],
        }
        return {
            **body,
            "source_ref": reference("workspace-initial-goal-postimage-source", body),
        }

    @property
    def plan(self):
        # Return detached neutral claims, not a mutable reference to private pins.
        return decode_goal_planning_initial_plan(canonical(self.to_wire()["plan"]))

    @property
    def carrier_bytes(self):
        return self.plan.carrier_bytes


def prepare_initial_planning_goal_postimage(preparation, permission):
    plan, wire = _current(preparation, permission)
    result = object.__new__(GoalPlanningPostimagePreparation)
    retained = (
        os.getpid(),
        preparation,
        permission,
        plan,
        plan.canonical_body,
        canonical(wire),
    )
    _PLANS[result] = retained
    _PINS[result] = retained
    result.require_current()
    return result


from aware_workspace_sdk.initial_authoring.goal_publication import _SOURCE_TYPES

_SOURCE_TYPES.add(GoalPlanningPostimagePreparation)
