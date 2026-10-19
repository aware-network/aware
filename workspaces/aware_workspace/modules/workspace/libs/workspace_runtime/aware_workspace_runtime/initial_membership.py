"""Exact membership admission by the original Workspace publication owner.

Live admission permits only the original exact repository effect. Projection is
separate; historical recovery never restores live permission or redispatch.
"""

from __future__ import annotations

import importlib
import os
import time
from dataclasses import dataclass, replace
from typing import Any

from aware_workspace_sdk.initial_authoring.membership import (
    InitialMembershipAdmission,
    InitialMembershipPlan,
    InitialMembershipRequest,
    _issue,
    _reservation,
    _retire_reservation,
    _state,
    membership_request,
)
from aware_workspace_sdk.initial_authoring.values import _canonical
from aware_workspace_sdk.repository_publication.values import (
    WorkspaceRepositoryCommitRequest,
)


def _input(owner, source):
    # Fixed original domain entrance, never a caller resolver or generic mapping.
    original = importlib.import_module("aware_workflow.project_initial_membership")
    if type(source) is not original.InitialProjectMembershipPreparation:
        raise ValueError("original_initial_membership_source_required")
    return original.require_membership_publication_input(owner, source)


@dataclass
class InitialMembershipState:
    owner: Any
    workspace_plan: Any
    source: Any
    request: Any
    frozen_request: bytes
    frozen_binding: bytes
    pid: int
    phase: str = "planned"
    admission: bytes | None = None
    deadline: float | None = None
    work: Any = None

    def pins(self):
        return (
            self.owner,
            self.workspace_plan,
            self.source,
            self.request,
            self.frozen_request,
            self.frozen_binding,
            self.pid,
        )

    def validate(self, *, current=False):
        self.owner._current()
        binding = self.workspace_plan.binding
        if (
            self.pid != os.getpid()
            or type(self.request) is not InitialMembershipRequest
            or self.owner._snapshot_handle(self.workspace_plan).purpose
            != "initial_membership"
            or _canonical(self.request.to_wire()) != self.frozen_request
            or _canonical(self.owner._detached_binding(binding)) != self.frozen_binding
            or binding.execution_id != self.owner._execution
            or binding.provider_ref != self.owner._provider_ref
            or binding.provider_generation != self.owner._generation
        ):
            raise ValueError("initial_membership_plan_mutated")
        if current and _canonical(_input(self.owner, self.source)) != _canonical(
            self.request.source
        ):
            raise ValueError("initial_membership_plan_source_changed")


def plan_initial_membership(owner, source, *, idempotency_key):
    owner._current()
    supplied = _input(owner, source)
    request = membership_request(supplied, idempotency_key)
    plan = owner._plan_repository_operation(
        WorkspaceRepositoryCommitRequest(
            supplied["repository_root"],
            (supplied["target_path"],),
            "Attach created Goal to Project",
            request.request_ref,
        ),
        initial_membership=supplied,
    )
    if plan.binding.expected_head != supplied["expected_head"]:
        raise ValueError("initial_membership_source_advanced")
    state = InitialMembershipState(
        owner,
        plan,
        source,
        request,
        _canonical(request.to_wire()),
        _canonical(owner._detached_binding(plan.binding)),
        os.getpid(),
    )
    state.validate(current=True)
    return _issue(owner, state, InitialMembershipPlan)


def admit_initial_membership(owner, plan):
    state = _state(plan, InitialMembershipPlan)
    if state.owner is not owner:
        raise ValueError("initial_membership_foreign_owner")
    state.validate(current=True)
    if state.phase != "planned" or state.workspace_plan.phase != "planned":
        raise ValueError("initial_membership_plan_terminal")
    state.phase = "reserving"
    token = _reservation(owner, state)
    try:
        record = owner._physical.reserve_initial_membership(token)
    except BaseException:
        state.phase = "uncertain"
        raise
    finally:
        _retire_reservation(token)
    if (
        _canonical(record["request"]) != state.frozen_request
        or _canonical(record["binding"]) != state.frozen_binding
    ):
        state.phase = "uncertain"
        raise ValueError("initial_membership_original_return_mismatch")
    state.admission = _canonical(record)
    state.deadline = time.monotonic() + 300
    state.work = owner._initial_configuration_work(state.workspace_plan)
    state.work.purpose = "initial_membership"
    owner._work_by_plan[state.workspace_plan] = state.work
    state.phase = "admitted"
    return _issue(owner, state, InitialMembershipAdmission)


def require_initial_membership_work(owner, admission):
    state = _state(admission, InitialMembershipAdmission)
    if state.owner is not owner or state.phase != "publishing":
        raise ValueError("initial_membership_dispatch_not_admitted")
    return state.work


def require_initial_membership_dispatch(port, attempt, admission):
    state = _state(admission, InitialMembershipAdmission)
    if (
        state.owner._physical is not port
        or state.phase != "publishing"
        or state.work.enrollment is not attempt
        or _canonical(attempt.record) != state.admission
        or state.deadline is None
        or time.monotonic() >= state.deadline
    ):
        raise ValueError("initial_membership_dispatch_not_admitted")
    state.validate(current=True)
    return state.request


def publish_initial_membership(owner, admission):
    state = _state(admission, InitialMembershipAdmission)
    if state.owner is not owner:
        raise ValueError("initial_membership_foreign_owner")
    result = None
    try:
        with owner._physical.initial_membership_attempt(state.request) as attempt:
            if _canonical(attempt.record) != state.admission:
                raise ValueError("initial_membership_retained_admission_changed")
            recovered = attempt.recover()
            # The original effect wins over expiry or unrelated later HEAD.
            if recovered["disposition"] == "recorded":
                result = recovered["original_result"]
                return result
            if state.phase != "admitted" or recovered["disposition"] != "pending":
                raise ValueError("initial_membership_uncertain_no_redispatch")
            if state.deadline is None or time.monotonic() >= state.deadline:
                raise ValueError("initial_membership_admission_expired")
            state.validate(current=True)
            state.phase = "publishing"
            state.work.enrollment = attempt
            try:
                result = owner._execute_repository_operation(
                    state.workspace_plan, admission, initial_membership=True
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
            + ("initial_membership_terminal_fence_failed", type(error).__name__),
        )


def recover_initial_membership(owner, request, *, project=False, read_only=False):
    owner._current()
    if type(request) is not InitialMembershipRequest:
        raise ValueError("exact_initial_membership_request_required")
    request.to_wire()
    if request.execution_id != owner._execution:
        raise ValueError("initial_membership_recovery_execution_mismatch")
    original = projected = None
    try:
        with owner._physical.initial_membership_attempt(request) as attempt:
            original = attempt.recover()
            if project:
                projected = attempt.project_membership(read_only=read_only)
            owner._current()
    except (ValueError, OSError, RuntimeError) as error:
        if not project or original is None:
            raise
        projected = {
            "projection_state": "uncertain",
            "projection": None,
            "diagnostics": (str(error),),
        }
    if original is None:
        raise ValueError("initial_membership_original_result_required")
    return {
        **original,
        **(projected or {}),
        "goal_creation_publication": request.source["preparation"]["source"][
            "goal_creation_publication"
        ],
    }


def observe_initial_membership_admission(owner, request):
    owner._current()
    if (
        type(request) is not InitialMembershipRequest
        or request.execution_id != owner._execution
    ):
        raise ValueError("initial_membership_observation_request_mismatch")
    request.to_wire()
    with owner._physical.initial_membership_attempt(request) as attempt:
        owner._current()
        record = attempt.observe_admission()
    return {
        "admission": record,
        "live_admission": "not_restored",
        "dispatch": "unavailable",
        "authorizes_redispatch": False,
    }


from aware_workspace_sdk.initial_authoring.membership import _STATE_TYPES

_STATE_TYPES.add(InitialMembershipState)
