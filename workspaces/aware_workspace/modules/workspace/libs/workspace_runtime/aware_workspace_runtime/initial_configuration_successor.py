"""Neutral one-successor admission/recovery, through the original publisher."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, replace
from typing import Any

from aware_workspace_sdk.initial_authoring.configuration_successor import (
    _TYPES,
    MESSAGE,
    ConfigurationSuccessorAdmission,
    ConfigurationSuccessorPlan,
    InitialConfigurationSuccessorRequest,
    _issue,
    _reservation,
    _retire,
    _state,
    successor_request,
    validate_admission,
    validate_origin,
    validate_predecessor,
)
from aware_workspace_sdk.initial_authoring.values import _canonical
from aware_workspace_sdk.repository_publication.codec import (
    repository_publication_value_from_payload,
)
from aware_workspace_sdk.repository_publication.values import (
    WorkspaceRepositoryCommitRequest,
    WorkspaceRepositoryCommitResult,
)


def require_terminal_predecessor(bundle):
    validate_predecessor(bundle)
    result = repository_publication_value_from_payload(
        WorkspaceRepositoryCommitResult, bundle["publication"]["original_result"]
    )
    writer = result.original_writer_report
    if (
        result.publication_state != "not_published"
        or not result.ledger_complete
        or result.admission_completion != "completed"
        or result.cleanup_state != "completed"
        or result.lock_release is None
        or result.lock_release.repository_lock_release != "confirmed_released"
        or result.commit_hash is not None
        or result.candidate_commit is not None
        or result.reference_update != "not_run"
        or result.index_projection != "not_run"
        or result.effects
        or writer is None
        or not writer.shared_index_unchanged
        or writer.status != "failed"
        or writer.reference_update != "not_run"
    ):
        raise ValueError("configuration_successor_predecessor_not_terminal_unpublished")


@dataclass
class SuccessorState:
    owner: Any
    workspace_plan: Any
    request: InitialConfigurationSuccessorRequest
    request_wire: bytes
    binding_wire: bytes
    pid: int
    phase: str = "planned"
    admission_wire: bytes | None = None
    work: Any = None
    deadline: float | None = None

    def pins(self):
        return (
            self.owner,
            self.workspace_plan,
            self.request,
            self.request_wire,
            self.binding_wire,
            self.pid,
        )

    def validate(self):
        self.owner._current()
        binding = self.workspace_plan.binding
        if (
            self.pid != os.getpid()
            or type(self.request) is not InitialConfigurationSuccessorRequest
            or _canonical(self.request.to_wire()) != self.request_wire
            or _canonical(self.owner._detached_binding(binding)) != self.binding_wire
            or self.owner._snapshot_handle(self.workspace_plan).purpose
            != "initial_configuration_successor"
            or binding.execution_id != self.owner._execution
            or binding.provider_ref != self.owner._provider_ref
            or binding.provider_generation != self.owner._generation
        ):
            raise ValueError("configuration_successor_plan_mutated")
        require_terminal_predecessor(self.request.to_wire()["predecessor"])


def prepare(owner):
    owner._current()
    observed = owner._physical.observe_initial_configuration_predecessor()
    require_terminal_predecessor(observed["predecessor"])
    request = successor_request(observed["predecessor"], observed["source"])
    if request.execution_id != owner._execution:
        raise ValueError("configuration_successor_execution_mismatch")
    plan = owner._plan_repository_operation(
        WorkspaceRepositoryCommitRequest(
            observed["source"]["repository_root"],
            ("aware.protocol.toml",),
            MESSAGE,
            request.request_ref,
        ),
        initial_configuration_successor=request.to_wire(),
    )
    state = SuccessorState(
        owner,
        plan,
        request,
        _canonical(request.to_wire()),
        _canonical(owner._detached_binding(plan.binding)),
        os.getpid(),
    )
    return _issue(state, ConfigurationSuccessorPlan)


def admit(owner, plan):
    state = _state(plan, ConfigurationSuccessorPlan)
    if state.owner is not owner or state.phase != "planned":
        raise ValueError("configuration_successor_plan_terminal_or_foreign")
    state.phase = "reserving"
    state.deadline = time.monotonic() + 300
    claim = _reservation(state)
    try:
        record = owner._physical.reserve_initial_configuration_successor(claim)
    finally:
        _retire(claim)
    validate_admission(record, successor=True)
    if (
        _canonical(record["request"]) != state.request_wire
        or _canonical(record["binding"]) != state.binding_wire
    ):
        raise ValueError("configuration_successor_admission_return_mismatch")
    state.admission_wire = _canonical(record)
    state.work = owner._initial_configuration_work(state.workspace_plan)
    state.work.purpose = "initial_configuration_successor"
    owner._work_by_plan[state.workspace_plan] = state.work
    state.phase = "admitted"
    return _issue(state, ConfigurationSuccessorAdmission)


def require_work(owner, admission):
    state = _state(admission, ConfigurationSuccessorAdmission)
    if state.owner is not owner or state.phase != "publishing":
        raise ValueError("configuration_successor_dispatch_not_admitted")
    return state.work


def publish(owner, admission):
    state = _state(admission, ConfigurationSuccessorAdmission)
    if state.owner is not owner:
        raise ValueError("configuration_successor_foreign_owner")
    result = None
    try:
        with owner._physical.initial_configuration_successor_attempt(
            state.request
        ) as attempt:
            if _canonical(attempt.record) != state.admission_wire:
                raise ValueError("configuration_successor_retained_admission_changed")
            recovered = attempt.recover()
            if recovered["disposition"] == "recorded":
                result = recovered["original_result"]
                return result
            if state.phase != "admitted" or recovered["disposition"] != "pending":
                raise ValueError("configuration_successor_uncertain_no_redispatch")
            if state.deadline is None or time.monotonic() >= state.deadline:
                raise ValueError("configuration_successor_admission_expired")
            attempt.require_current()
            state.phase = "publishing"
            state.work.enrollment = attempt
            try:
                result = owner._execute_repository_operation(
                    state.workspace_plan,
                    admission,
                    initial_configuration_successor=True,
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
            + ("configuration_successor_terminal_fence_failed", type(error).__name__),
        )


def observe(owner, *, project=False, read_only=False):
    owner._current()
    original = projected = None
    request = None
    try:
        with owner._physical.initial_configuration_successor_attempt(None) as attempt:
            request = InitialConfigurationSuccessorRequest.from_wire(
                attempt.record["request"]
            )
            require_terminal_predecessor(request.to_wire()["predecessor"])
            if request.execution_id != owner._execution:
                raise ValueError("configuration_successor_execution_mismatch")
            original = attempt.recover()
            if project:
                projected = attempt.project_configuration(read_only=read_only)
            owner._current()
    except (ValueError, OSError, RuntimeError) as error:
        if not project or original is None or request is None:
            raise
        return {
            **original,
            "request": request.to_wire(),
            "projection_state": "uncertain",
            "projection": None,
            "original_projection_result": projected,
            "diagnostics": (str(error),),
            "authorizes_redispatch": False,
        }
    if request is None or original is None:
        raise ValueError("configuration_successor_observation_unavailable")
    result = {**original, "request": request.to_wire(), "authorizes_redispatch": False}
    return {**result, **projected} if projected is not None else result


def origin(owner, *, current=False):
    owner._current()
    wire = owner._physical.observe_initial_configuration_origin(current=current)
    validate_origin(wire)
    if wire["enrollment"]["execution_id"] != owner._execution:
        raise ValueError("configuration_origin_execution_mismatch")
    if wire["kind"] == "successor":
        require_terminal_predecessor(wire["predecessor"])
    owner._current()
    return wire


_TYPES.add(SuccessorState)
