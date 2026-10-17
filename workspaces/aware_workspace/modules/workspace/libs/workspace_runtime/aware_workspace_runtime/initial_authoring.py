"""Neutral enrollment correlation; filesystem policy and durability stay in FS.

Enrollment is a prerequisite, not exact-effect publication admission. Only the
distinct configuration admission can enter the selected shared writer branch;
neither enrollment nor configuration admission can spend an Issue lease.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from aware_workspace_sdk.initial_authoring.values import (
    InitialAuthoringEnrollmentEvidence,
    InitialConfigurationRequest,
)
from aware_workspace_sdk.repository_publication.authority import (
    WorkspaceRepositoryCommitPlan,
)


class InitialAuthoringEnrollmentState:
    def __init__(self, owner, evidence):
        self._owner = owner
        self._evidence = InitialAuthoringEnrollmentEvidence.from_wire(
            evidence.to_wire()
        )

    def observe(self):
        self._owner._current()
        evidence = self._owner._physical.observe_initial_authoring_enrollment()
        if evidence != self._evidence:
            raise ValueError("initial_authoring_original_enrollment_changed")
        return InitialAuthoringEnrollmentEvidence.from_wire(evidence.to_wire())


def enroll_from_original_preparation(owner, preparation_client):
    from aware_workspace_sdk.initial_authoring.authority import (
        _issue_enrollment_claim,
        _issue_initial_enrollment,
        _retire_enrollment_claim,
    )

    owner._current()
    # The SDK supplies its retained successful original dispatch. Neither a
    # decoded preparation result nor runtime.last_original_result is accepted.
    claim = _issue_enrollment_claim(owner, preparation_client)
    try:
        evidence = owner._physical.enroll_initial_authoring(claim)
    finally:
        _retire_enrollment_claim(claim)
    owner._current()
    return _issue_initial_enrollment(
        owner, InitialAuthoringEnrollmentState(owner, evidence)
    )


def restore_original_enrollment(owner):
    from aware_workspace_sdk.initial_authoring.authority import (
        _issue_initial_enrollment,
    )

    owner._current()
    evidence = owner._physical.observe_initial_authoring_enrollment(
        confirm_durability=True
    )
    if evidence.execution_id != owner._execution:
        raise ValueError("initial_authoring_execution_mismatch")
    owner._current()
    return _issue_initial_enrollment(
        owner, InitialAuthoringEnrollmentState(owner, evidence)
    )


from aware_workspace_sdk.initial_authoring.authority import _STATE_TYPES

_STATE_TYPES.add(InitialAuthoringEnrollmentState)


def _configuration(owner, protocol_plan):
    # The explicitly selected original physical provider qualifies the concrete
    # producer. Neutral orchestration does not import a filesystem/Protocol rail.
    return owner._physical.require_initial_configuration_source(protocol_plan)


@dataclass
class InitialConfigurationState:
    owner: Any
    workspace_plan: WorkspaceRepositoryCommitPlan
    protocol_plan: object
    request: InitialConfigurationRequest
    frozen_wire: bytes
    frozen_binding: bytes
    phase: str = "planned"
    work: object = None
    admission_wire: bytes | None = None
    expires_monotonic: float | None = None

    def validate(self):
        from aware_workspace_sdk.initial_authoring.values import _canonical

        self.owner._current()
        if (
            _canonical(self.request.to_wire()) != self.frozen_wire
            or _canonical(self.owner._detached_binding(self.workspace_plan.binding))
            != self.frozen_binding
            or self.workspace_plan.binding.provider_ref != self.owner._provider_ref
            or self.workspace_plan.binding.provider_generation != self.owner._generation
            or self.workspace_plan.binding.execution_id != self.owner._execution
            or _configuration(self.owner, self.protocol_plan).to_wire()
            != self.request.to_wire()["configuration"]
        ):
            raise ValueError("initial_configuration_plan_mutated")


def plan_initial_configuration(owner, enrollment, protocol_plan, idempotency_key):
    from aware_workspace_sdk.initial_authoring.authority import (
        _ENROLLMENTS,
        InitialAuthoringEnrollment,
        InitialConfigurationPlan,
        _issue_configuration_handle,
    )
    from aware_workspace_sdk.initial_authoring.values import (
        _canonical,
        configuration_request,
    )
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryCommitRequest,
    )

    owner._current()
    state = (
        _ENROLLMENTS.get(enrollment)
        if type(enrollment) is InitialAuthoringEnrollment
        else None
    )
    if state is None or state._owner is not owner:
        raise ValueError("original_initial_authoring_enrollment_required")
    evidence = state.observe()
    config = _configuration(owner, protocol_plan)
    if config.repository_root != evidence.repository_root:
        raise ValueError("initial_configuration_root_mismatch")
    request = configuration_request(evidence, config, idempotency_key)
    workspace_plan = owner._plan_repository_operation(
        WorkspaceRepositoryCommitRequest(
            config.repository_root,
            ("aware.protocol.toml",),
            "Initialize Project-capable Protocol configuration",
            request.request_ref,
        ),
        initial_configuration=config.content,
    )
    result = InitialConfigurationState(
        owner,
        workspace_plan,
        protocol_plan,
        request,
        _canonical(request.to_wire()),
        _canonical(owner._detached_binding(workspace_plan.binding)),
    )
    return _issue_configuration_handle(owner, result, InitialConfigurationPlan)


def admit_initial_configuration(owner, plan):
    from aware_workspace_sdk.initial_authoring.authority import (
        InitialConfigurationAdmission,
        InitialConfigurationPlan,
        _configuration_state,
        _issue_configuration_handle,
        _issue_configuration_reservation,
        _retire_configuration_reservation,
    )
    from aware_workspace_sdk.initial_authoring.values import _canonical

    state = _configuration_state(owner, plan, InitialConfigurationPlan)
    if state.phase != "planned" or state.workspace_plan.phase != "planned":
        raise ValueError("initial_configuration_plan_terminal")
    # Reserve intent before issuing the distinct live admission. A failed or
    # interrupted reservation is never silently rewritten or redispatched.
    state.phase = "reserving"
    state.expires_monotonic = time.monotonic() + 300
    reservation = _issue_configuration_reservation(owner, state)
    try:
        record = owner._physical.reserve_initial_configuration(reservation)
    finally:
        _retire_configuration_reservation(reservation)
    if record["request"] != state.request.to_wire() or record[
        "binding"
    ] != owner._detached_binding(state.workspace_plan.binding):
        raise ValueError("initial_admission_original_return_mismatch")
    state.admission_wire = _canonical(record)
    state.work = owner._initial_configuration_work(state.workspace_plan)
    owner._work_by_plan[state.workspace_plan] = state.work
    state.phase = "admitted"
    return _issue_configuration_handle(owner, state, InitialConfigurationAdmission)


def require_initial_configuration_work(owner, admission):
    from aware_workspace_sdk.initial_authoring.authority import (
        InitialConfigurationAdmission,
        _configuration_state,
    )

    state = _configuration_state(owner, admission, InitialConfigurationAdmission)
    if state.phase != "publishing":
        raise ValueError("initial_configuration_dispatch_not_admitted")
    return state.work


def publish_initial_configuration(owner, admission):
    from dataclasses import replace

    from aware_workspace_sdk.initial_authoring.authority import (
        InitialConfigurationAdmission,
        _configuration_state,
    )
    from aware_workspace_sdk.initial_authoring.values import _canonical

    state = _configuration_state(owner, admission, InitialConfigurationAdmission)
    result = None
    try:
        with owner._physical.initial_configuration_attempt(state.request) as attempt:
            if _canonical(attempt.record) != state.admission_wire:
                raise ValueError("initial_admission_retained_content_changed")
            recovered = attempt.recover()
            if recovered["disposition"] == "recorded":
                result = recovered["original_result"]
                return result
            if state.phase != "admitted" or recovered["disposition"] != "pending":
                raise ValueError("initial_configuration_uncertain_no_redispatch")
            if (
                state.expires_monotonic is None
                or time.monotonic() >= state.expires_monotonic
            ):
                raise ValueError("initial_configuration_admission_expired")
            state.phase = "publishing"
            state.work.enrollment = attempt
            try:
                result = owner._execute_repository_operation(
                    state.workspace_plan, admission, initial_configuration=True
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
            + ("initial_attempt_terminal_fence_failed", type(error).__name__),
        )


def recover_initial_configuration(owner, protocol_plan, idempotency_key):
    from aware_workspace_sdk.initial_authoring.values import configuration_request

    owner._current()
    evidence = owner._physical.observe_initial_authoring_enrollment(_attempt=True)
    if evidence.execution_id != owner._execution:
        raise ValueError("initial_authoring_execution_mismatch")
    config = _configuration(owner, protocol_plan)
    request = configuration_request(evidence, config, idempotency_key)
    with owner._physical.initial_configuration_attempt(request) as attempt:
        result = attempt.recover()
        owner._current()
        return result


from aware_workspace_sdk.initial_authoring.authority import _CONFIGURATION_TYPES

_CONFIGURATION_TYPES.add(InitialConfigurationState)
