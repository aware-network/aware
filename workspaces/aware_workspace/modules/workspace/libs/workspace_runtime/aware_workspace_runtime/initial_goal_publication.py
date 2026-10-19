"""Exact initial Goal effect through the original Workspace publication engine.

Goal meaning and physical effects stay with their original owners. Explicit
projection is separate from CAS; membership is not implemented. Live admissions
and historical recovery remain different entrances.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, replace
from typing import Any

from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationAdmission,
    InitialGoalPublicationPlan,
    InitialGoalPublicationRequest,
    _issue,
    _require_source,
    _reservation,
    _retire_reservation,
    _state,
    goal_publication_request,
)
from aware_workspace_sdk.initial_authoring.values import _canonical
from aware_workspace_sdk.repository_publication.values import (
    WorkspaceRepositoryCommitRequest,
)


@dataclass
class InitialGoalPublicationState:
    owner: Any
    workspace_plan: Any
    source: Any
    request: InitialGoalPublicationRequest
    frozen_wire: bytes
    frozen_binding: bytes
    pid: int
    phase: str = "planned"
    work: Any = None
    admission_wire: bytes | None = None
    deadline: float | None = None

    def pins(self):
        # Lifecycle fields are mutable only through this original orchestration.
        return (
            self.owner,
            self.workspace_plan,
            self.source,
            self.request,
            self.frozen_wire,
            self.frozen_binding,
            self.pid,
        )

    def validate(self, *, current=False):
        self.owner._current()
        binding = self.workspace_plan.binding
        if (
            self.pid != os.getpid()
            or type(self.request) is not InitialGoalPublicationRequest
            or self.owner._snapshot_handle(self.workspace_plan).purpose
            != "initial_goal"
            or _canonical(self.request.to_wire()) != self.frozen_wire
            or _canonical(self.owner._detached_binding(binding)) != self.frozen_binding
            or binding.provider_ref != self.owner._provider_ref
            or binding.provider_generation != self.owner._generation
            or binding.execution_id != self.owner._execution
        ):
            raise ValueError("initial_goal_publication_plan_mutated")
        if current and _canonical(
            _require_source(self.owner, self.source)
        ) != _canonical(self.request.source):
            raise ValueError("initial_goal_publication_source_changed")


def plan_initial_goal(owner, source):
    owner._current()
    supplied = _require_source(owner, source)
    request = goal_publication_request(
        supplied, supplied["intent_permission"]["idempotency_key"]
    )
    plan = owner._plan_repository_operation(
        WorkspaceRepositoryCommitRequest(
            supplied["repository_root"],
            (supplied["target_path"],),
            "Create Proposed Goal intent",
            request.request_ref,
        ),
        initial_goal=supplied,
    )
    state = InitialGoalPublicationState(
        owner,
        plan,
        source,
        request,
        _canonical(request.to_wire()),
        _canonical(owner._detached_binding(plan.binding)),
        os.getpid(),
    )
    if plan.binding.expected_head != supplied["expected_head"]:
        raise ValueError("initial_goal_publication_source_advanced")
    state.validate(current=True)
    return _issue(owner, state, InitialGoalPublicationPlan)


def admit_initial_goal(owner, plan):
    state = _state(plan, InitialGoalPublicationPlan)
    if state.owner is not owner:
        raise ValueError("initial_goal_publication_foreign_owner")
    state.validate(current=True)
    if state.phase != "planned" or state.workspace_plan.phase != "planned":
        raise ValueError("initial_goal_publication_plan_terminal")
    state.phase, state.deadline = "reserving", time.monotonic() + 300
    claim = _reservation(owner, state)
    try:
        record = owner._physical.reserve_initial_goal(claim)
    finally:
        _retire_reservation(claim)
    if (
        _canonical(record["request"]) != state.frozen_wire
        or _canonical(record["binding"]) != state.frozen_binding
    ):
        raise ValueError("initial_goal_admission_original_return_mismatch")
    state.admission_wire = _canonical(record)
    state.work = owner._initial_configuration_work(state.workspace_plan)
    state.work.purpose = "initial_goal"
    owner._work_by_plan[state.workspace_plan] = state.work
    state.phase = "admitted"
    return _issue(owner, state, InitialGoalPublicationAdmission)


def require_initial_goal_work(owner, admission):
    state = _state(admission, InitialGoalPublicationAdmission)
    if state.owner is not owner or state.phase != "publishing":
        raise ValueError("initial_goal_dispatch_not_admitted")
    return state.work


def publish_initial_goal(owner, admission):
    state = _state(admission, InitialGoalPublicationAdmission)
    if state.owner is not owner:
        raise ValueError("initial_goal_publication_foreign_owner")
    result = None
    try:
        with owner._physical.initial_goal_attempt(state.request) as attempt:
            if _canonical(attempt.record) != state.admission_wire:
                raise ValueError("initial_goal_admission_retained_content_changed")
            recovered = attempt.recover()
            # Immutable original effect precedes current-source/expiry refusal.
            if recovered["disposition"] == "recorded":
                result = recovered["original_result"]
                return result
            if state.phase != "admitted" or recovered["disposition"] != "pending":
                raise ValueError("initial_goal_uncertain_no_redispatch")
            if state.deadline is None or time.monotonic() >= state.deadline:
                raise ValueError("initial_goal_publication_admission_expired")
            state.validate(current=True)
            state.phase = "publishing"
            state.work.enrollment = attempt
            try:
                result = owner._execute_repository_operation(
                    state.workspace_plan,
                    admission,
                    initial_goal=True,
                )
                return result
            finally:
                state.phase = "spent"
    except BaseException as error:
        if result is None:
            raise
        return replace(
            result,
            ledger_complete=False,
            admission_completion="unknown",
            diagnostics=result.diagnostics
            + ("initial_goal_terminal_fence_failed", type(error).__name__),
        )


def recover_initial_goal(owner, request, *, project=False, read_only=False):
    owner._current()
    if type(request) is not InitialGoalPublicationRequest:
        raise ValueError("exact_initial_goal_publication_request_required")
    request.to_wire()
    if request.execution_id != owner._execution:
        raise ValueError("initial_goal_recovery_execution_mismatch")
    original = projected = None
    try:
        with owner._physical.initial_goal_attempt(request) as attempt:
            original = attempt.recover()
            if project:
                if original["disposition"] != "recorded":
                    raise ValueError("initial_goal_original_result_required")
                projected = attempt.project_goal(read_only=read_only)
            owner._current()
    except (ValueError, OSError, RuntimeError) as error:
        if not project or original is None:
            raise
        return {
            **original,
            "projection_state": "uncertain",
            "projection": None,
            "original_projection_result": projected,
            "diagnostics": (str(error),),
        }
    if original is None:
        raise ValueError("initial_goal_original_observation_unavailable")
    if not project:
        return original
    if projected is None:
        raise ValueError("initial_goal_projection_observation_unavailable")
    return {**original, **projected}


from aware_workspace_sdk.initial_authoring.goal_publication import _STATE_TYPES

_STATE_TYPES.add(InitialGoalPublicationState)
